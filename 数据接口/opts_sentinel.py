import ee
import geemap
import numpy as np
import pandas as pd
from typing import Union, List, Tuple

class SentinelProcessor:
    def __init__(self):
        """
        初始化 GEE。第一次运行需要根据提示在浏览器进行验证。
        """
        try:
            ee.Initialize()
            print("Google Earth Engine 初始化成功。")
        except Exception as e:
            print("GEE 初始化失败，尝试验证...")
            ee.Authenticate()
            ee.Initialize(project='geeproj-476712') # 改成自己的

    def get_sentinel_data(
        self, 
        location: Union[List[float], Tuple[float, float], List[float]], 
        date_range: Tuple[str, str], 
        bands: List[str] = ['B4', 'B3', 'B2'],
        max_cloud_cover: int = 20
    ) -> np.ndarray:
        """
        核心函数：查询、处理并返回 Sentinel-2 的 Numpy 数组。
        
        参数:
            location: 
                - 如果是点位: [lon, lat]
                - 如果是区域: [min_lon, min_lat, max_lon, max_lat] (左上右下 或 左下右上均可，代码会自动处理)
            date_range: ('2023-01-01', '2023-01-31')
            bands: 需要的波段，默认 RGB ('B4', 'B3', 'B2')
            max_cloud_cover: 筛选影像的最大云量百分比
            
        返回:
            numpy.ndarray: 形状为 (Height, Width, Bands) 的图像矩阵
        """
        
        # 1. 解析地理位置输入
        roi, is_point = self._parse_location(location)
        
        # 2. 构建影像集合 (Sentinel-2 Level-2A 地表反射率)
        # 按照云量排序，优先选云少的
        collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                      .filterDate(date_range[0], date_range[1])
                      .filterBounds(roi)
                      .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', max_cloud_cover))
                      .sort('CLOUDY_PIXEL_PERCENTAGE'))

        # 3. 检查并展示可用性
        count = collection.size().getInfo()
        if count == 0:
            print(f"⚠️ 在 {date_range} 期间该区域无符合云量要求的影像。")
            return None
        
        print(f"✅ 查询成功：找到 {count} 张可用影像。正在展示最优的前5张信息：")
        self._print_metadata(collection, limit=5)

        # 4. 数据处理（拼接 或 裁剪）
        target_image = None
        
        if is_point:
            # === 点位模式 ===
            # 取云量最小的一张
            best_image = collection.first()
            print("🚀 正在处理：选取云量最小的单张影像，并裁剪 1000x1000 像素...")
            
            # 2000像素 * 10米分辨率 = 20000米范围
            # 以点为中心，创建一个 20km 宽高的缓冲区对应的矩形
            # 注意：buffer 的单位是米
            buffer_dist = 5000  # 半径 10km
            geometry = roi.buffer(buffer_dist).bounds()
            
            # 裁剪影像
            target_image = best_image.select(bands).clip(geometry)
            
        else:
            # === 区域模式 ===
            # 将所有筛选出的影像进行拼接 (Mosaic)
            # mosaic() 会将集合中的图像层叠，位于顶层的像素（默认是集合中最后的）会覆盖底层的。
            # 为了保证最清晰，通常使用 qualityMosaic 或 简单的 mosaic (结合云掩膜)
            # 这里使用简单的 mosaic，因为我们已经筛选过低云量
            print("🚀 正在处理：将区域内的影像进行拼接 (Mosaic)...")
            target_image = collection.select(bands).mosaic().clip(roi)
            geometry = roi

        # 5. 转化为 Numpy 数组
        # 使用 geemap 提取像素值。scale=10 代表 10米分辨率
        print("📥 正在下载数据并转换为 NumPy 数组 (这可能需要几秒钟)...")
        try:
            # geemap.ee_to_numpy 自动处理投影和重采样
            # default_value=0 用于填充无数据区域
            arr = geemap.ee_to_numpy(target_image, region=geometry, scale=10)
            
            if arr is None:
                raise ValueError("转换结果为空，可能是区域过大超过了 API 限制。")
                
            print(f"🎉 处理完成！返回数组形状: {arr.shape}")
            return arr
            
        except Exception as e:
            print(f"❌ 数据提取失败: {e}")
            return None

    def _parse_location(self, loc):
        """解析输入是点还是区域"""
        if len(loc) == 2:
            # 点位 [lon, lat]
            print(f"📍 检测到输入为点位: {loc}")
            return ee.Geometry.Point(loc), True
        elif len(loc) == 4:
            # 区域 [min_lon, min_lat, max_lon, max_lat]
            # 确保顺序正确，构建矩形
            x_coords = [loc[0], loc[2]]
            y_coords = [loc[1], loc[3]]
            bbox = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
            print(f"🗺️ 检测到输入为区域: {bbox}")
            return ee.Geometry.BBox(*bbox), False
        else:
            raise ValueError("输入格式错误。点位需要2个坐标，区域需要4个坐标。")

    def _print_metadata(self, collection, limit=5):
        """辅助函数：打印影像元数据"""
        # 获取列表信息 (只取需要的字段以加快速度)
        info_list = collection.limit(limit).reduceColumns(
            ee.Reducer.toList(3), ['system:id', 'CLOUDY_PIXEL_PERCENTAGE', 'system:time_start']
        ).get('list').getInfo()
        
        df = pd.DataFrame(info_list, columns=['Image ID', 'Cloud Cover (%)', 'Timestamp'])
        # 转换时间戳
        df['Date'] = pd.to_datetime(df['Timestamp'], unit='ms')
        df = df.drop(columns=['Timestamp'])
        print(df.to_string(index=False))
        print("-" * 50)

# --- 使用示例 ---
if __name__ == "__main__":
    processor = SentinelProcessor()

    # 示例 1: 输入点位 (北京故宫附近) -> 截取 2000x2000 像素
    point_loc = [116.397, 39.908] 
    
    # 示例 2: 输入区域 (一个小范围的矩形) -> 自动拼接
    area_loc = [116.35, 39.85, 116.45, 39.95]

    # 执行查询
    # 这里我们演示点位查询，获取 RGB 数据
    image_array = processor.get_sentinel_data(
        location=point_loc,
        date_range=('2023-05-01', '2023-09-01'), # 夏季植被丰富
        bands=['B4', 'B3', 'B2'], # Red, Green, Blue
        max_cloud_cover=10 # 只看少于10%云的
    )

    if image_array is not None:
        # image_array 的形状通常是 (Height, Width, Bands)
        # 我们可以用 matplotlib 简单看一下 (如果安装了 matplotlib)
        try:
            import matplotlib.pyplot as plt
            # 归一化用于显示 (Sentinel-2 数值通常在 0-3000 左右，最大 10000)
            display_arr = image_array.astype(float) / 3000.0 
            display_arr = np.clip(display_arr, 0, 1)
            
            plt.figure(figsize=(10, 10))
            plt.title("Sentinel-2 Retrieved Image")
            plt.imshow(display_arr)
            plt.axis('off')
            plt.show()
        except ImportError:
            print("未安装 matplotlib，跳过绘图。")