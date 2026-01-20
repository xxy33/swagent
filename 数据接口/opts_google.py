import io
import math
import numpy as np
from PIL import Image
import requests
import mercantile
from typing import Union, List, Tuple

class GoogleEarthDownloader:
    def __init__(self):
        # Google 卫星图源 (lyrs=s 代表只有卫星图，无标签)
        self.tile_url = "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}"
        # 伪装 Header 防止被拦截
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        print("🚀 Google Earth 高清影像下载器已就绪")

    def get_image_data(
        self, 
        location: Union[List[float], Tuple[float, float], List[float]], 
        zoom_level: int = 18,
        point_size: int = 2000
    ) -> np.ndarray:
        """
        核心函数：获取高清 Google Earth 影像并返回 Numpy 数组。
        注意：Google Earth 底图是静态的，无法筛选时间或云量。

        参数:
            location: 
                - 点位: [lon, lat]
                - 区域: [min_lon, min_lat, max_lon, max_lat]
            zoom_level: 缩放级别。18约为0.6m分辨率，19约为0.3m分辨率。
            point_size: 当输入为点位时，生成的图片像素宽/高 (默认 2000x2000)
            
        返回:
            numpy.ndarray: (Height, Width, 3) RGB 数组
        """
        
        # 1. 区分模式（点 vs 区域）并计算需要下载的瓦片范围
        if len(location) == 2:
            print(f"📍 模式: 单点截取 (中心: {location})")
            img = self._process_point(location[0], location[1], zoom_level, point_size)
        elif len(location) == 4:
            print(f"🗺️ 模式: 区域拼接 (范围: {location})")
            img = self._process_bbox(location, zoom_level)
        else:
            raise ValueError("输入格式错误。点位需2个坐标，区域需4个坐标。")

        if img is None:
            return None

        # 2. 转换为 Numpy 数组
        print("📥 正在转换为 NumPy 数组...")
        # 确保是 RGB 模式 (去除可能的 Alpha 通道)
        img_rgb = img.convert('RGB')
        arr = np.array(img_rgb)
        
        print(f"🎉 处理完成！返回数组形状: {arr.shape}, 分辨率级别: {zoom_level}")
        return arr

    def _process_point(self, lon, lat, zoom, size):
        """处理单点：计算该点在 zoom 级别的像素坐标，向四周扩展，拼接后裁剪"""
        # 获取中心点在世界像素坐标系(World Pixel)的位置
        # Google Maps tiles usually are 256x256
        
        # mercantile.tile 获取该经纬度所属的瓦片
        center_tile = mercantile.tile(lon, lat, zoom)
        
        # 为了保证裁剪出 size*size 的图，我们需要下载周围的瓦片
        # 粗略计算需要的瓦片数量（以中心瓦片为原点，向四周扩充）
        # 2000像素约等于 8 个 256像素的瓦片，所以向四周各扩 2-3 个瓦片足够
        buffer_tiles = math.ceil(size / 256 / 2) + 1
        
        min_x = center_tile.x - buffer_tiles
        max_x = center_tile.x + buffer_tiles
        min_y = center_tile.y - buffer_tiles
        max_y = center_tile.y + buffer_tiles
        
        # 下载并拼接
        stitched_img, (offset_x, offset_y) = self._download_and_stitch(min_x, max_x, min_y, max_y, zoom)
        
        # 计算中心经纬度在拼接大图中的精确像素位置
        # mercantile.xy_bounds 获取瓦片经纬度边界，这里比较复杂，
        # 我们采用相对简单的方法：计算中心点相对于左上角瓦片起点的像素偏移
        
        # 左上角瓦片的左上角经纬度
        nw_bounds = mercantile.bounds(min_x, min_y, zoom)
        # 将经纬度转为 Web Mercator 投影的米
        # 实际上直接用 pyproj 或者手动计算像素偏移更准，这里为了减少依赖，
        # 我们使用 mercantile 的工具计算像素坐标
        
        # 任何经纬度 -> 全局像素坐标
        # mercantile 不直接提供 latlon -> global pixel，但我们可以通过比例推算
        # 简单逻辑：在大图里，中心就在正中间吗？不一定。
        # 既然我们下载的是以 center_tile 为中心的 grid，
        # 那么中心点大致在 (img_width/2, img_height/2)，但需要微调瓦片内的偏移。
        
        # 更精确的裁剪逻辑：
        # 1. 获取中心点对应的 Global Pixel 坐标
        # 2. 获取左上角瓦片 (min_x, min_y) 的 Global Pixel 坐标
        # 3. 差值即为 crop_center
        
        # 这种计算比较繁琐，我们采用“重投影截取”的最优解思路：
        # 既然我们已经有了 stitched_img，它覆盖了足够大的范围。
        # 我们只需算出 lon/lat 在这张图上的相对位置。
        
        # 这里简化处理：下载范围是以 Tile 为单位的。
        # 计算 lat/lon 在 center_tile 内部的 offset
        # center_tile 的 bounds
        b = mercantile.bounds(center_tile)
        # width in longitude
        w_lon = b.east - b.west
        h_lat = b.north - b.south
        
        # 相对比例 (0-1)
        x_ratio = (lon - b.west) / w_lon
        y_ratio = (b.north - lat) / h_lat # 纬度越高 pixel y 越小
        
        # center_tile 在大图中的左上角位置
        tile_pixel_x = (center_tile.x - min_x) * 256
        tile_pixel_y = (center_tile.y - min_y) * 256
        
        # 绝对中心像素
        center_px_x = tile_pixel_x + (x_ratio * 256)
        center_px_y = tile_pixel_y + (y_ratio * 256)
        
        # 裁剪框
        left = center_px_x - (size // 2)
        top = center_px_y - (size // 2)
        right = left + size
        bottom = top + size
        
        return stitched_img.crop((left, top, right, bottom))

    def _process_bbox(self, bbox, zoom):
        """处理区域：计算覆盖该区域的所有瓦片，下载并拼接，最后裁剪到精确边界"""
        west, south, east, north = bbox
        
        # 获取覆盖该 bbox 的所有 tiles
        tiles = list(mercantile.tiles(west, south, east, north, zoom))
        
        if not tiles:
            return None
            
        min_x = min(t.x for t in tiles)
        max_x = max(t.x for t in tiles)
        min_y = min(t.y for t in tiles)
        max_y = max(t.y for t in tiles)
        
        print(f"📊 区域覆盖瓦片数: {(max_x-min_x+1)} x {(max_y-min_y+1)}")
        
        # 下载拼接
        stitched_img, _ = self._download_and_stitch(min_x, max_x, min_y, max_y, zoom)
        
        # 裁剪到精确的 bbox (去除瓦片边缘多余部分)
        # 计算左上角瓦片(min_x, min_y)的边界
        ul_bounds = mercantile.bounds(min_x, min_y, zoom)
        lr_bounds = mercantile.bounds(max_x, max_y, zoom)
        
        # 整个大图覆盖的经纬度范围
        img_west, img_north = ul_bounds.west, ul_bounds.north
        img_east, img_south = lr_bounds.east, lr_bounds.south
        
        # 整个大图的尺寸
        W, H = stitched_img.size
        
        # 线性插值计算裁剪位置 (假设墨卡托投影在局部是线性的，对于小区域误差可忽略)
        # 注意：这里简单的线性插值对于大范围可能有投影误差，但在 Zoom 18 级别通常可接受
        
        def get_px_x(lon):
            return int((lon - img_west) / (img_east - img_west) * W)
            
        def get_px_y(lat):
            # 纬度方向是反的 (北是0)
            # 墨卡托投影是非线性的，严格来说应该用墨卡托公式，
            # 但为了简化代码且在 Zoom 18 局部范围内，线性近似通常足够。
            # 如果需要极高精度，建议引入 pyproj 转换坐标。
            # 这里我们使用 mercantile 的 helper 来获取相对于左上角 tile 的 offset 会更准
            return int((img_north - lat) / (img_north - img_south) * H)

        # 更好的方法：计算 bbox 四个角对应的 Tile 像素坐标
        # 这里简化直接返回拼接图，或者用户根据需要自行裁剪
        # 为了演示完整性，做简单裁剪：
        
        left = get_px_x(west)
        right = get_px_x(east)
        # lat 越大 y 越小
        top = get_px_y(north) 
        bottom = get_px_y(south)
        
        return stitched_img.crop((left, top, right, bottom))

    def _download_and_stitch(self, min_x, max_x, min_y, max_y, zoom):
        """通用下载拼接逻辑"""
        width = (max_x - min_x + 1) * 256
        height = (max_y - min_y + 1) * 256
        
        result_img = Image.new('RGB', (width, height))
        
        total_tiles = (max_x - min_x + 1) * (max_y - min_y + 1)
        processed = 0
        print(f"🔄 开始下载 {total_tiles} 个瓦片...")

        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                url = self.tile_url.format(x=x, y=y, z=zoom)
                try:
                    response = requests.get(url, headers=self.headers, timeout=10)
                    if response.status_code == 200:
                        tile_img = Image.open(io.BytesIO(response.content))
                        
                        # 计算粘贴位置
                        paste_x = (x - min_x) * 256
                        paste_y = (y - min_y) * 256
                        result_img.paste(tile_img, (paste_x, paste_y))
                    else:
                        print(f"⚠️ 下载失败 ({x},{y}): {response.status_code}")
                except Exception as e:
                    print(f"❌ 网络错误 ({x},{y}): {e}")
                
                processed += 1
                if processed % 10 == 0:
                    print(f"   进度: {processed}/{total_tiles}")
                    
        return result_img, (min_x, min_y)

# --- 使用示例 ---
if __name__ == "__main__":
    downloader = GoogleEarthDownloader()

    # 示例 1: 故宫某点，获取 2000x2000 像素
    # Zoom 19 大约对应 0.3米/像素，非常清晰
    # point_loc = [116.397, 39.908] 
    point_loc = [116.327307,39.995698]
    
    img_array = downloader.get_image_data(
        location=point_loc,
        zoom_level=19,  # 19级非常清晰，1m需求通常18级足够
        point_size=1000
    )

    if img_array is not None:
        try:
            import matplotlib.pyplot as plt
            plt.figure(figsize=(10, 10))
            plt.title("Google Earth High-Res (Zoom 19)")
            plt.imshow(img_array)
            plt.axis('off')
            plt.show()
            
            # 你可以直接使用 img_array 进行深度学习或其他处理
            # print(img_array.mean())
        except ImportError:
            pass
            
    # 示例 2: 区域下载 (注意：区域太大下载会很慢)
    # area_loc = [116.39, 39.90, 116.40, 39.91]
    # area_arr = downloader.get_image_data(area_loc, zoom_level=18)