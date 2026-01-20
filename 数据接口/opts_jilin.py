import io
import math
import numpy as np
from PIL import Image
import requests
import mercantile
from typing import Union, List, Tuple

class JL1MallDownloader:
    def __init__(self):
        """
        初始化吉林一号商城下载器
        """
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://www.jl1mall.com/"  # 必须添加，否则可能403
        }
        
        # 2024年图源 (使用 {-y} 占位符)
        self.url_template_2024 = (
            "https://api.jl1mall.com/getMap/{z}/{x}/{-y}?"
            "mk=3ddec00f5f435270285ffc7ad1a60ce5&tk=125f1f480b8225a04df00a5c8a3c8fbb"
        )
        
        # 2023年图源 (使用 {-y} 占位符)
        self.url_template_2023 = (
            "https://api.jl1mall.com/getMap/{z}/{x}/{-y}?"
            "mk=73ad26c4aa6957eef051ecc5a15308b4&tk=125f1f480b8225a04df00a5c8a3c8fbb"
        )

        self.url_template_2022 =(
            "https://api.jl1mall.com/getMap/{z}/{x}/{-y}?"
            "mk=bd60ffe96379e0c9cbc1be02b06e3622&tk=125f1f480b8225a04df00a5c8a3c8fbb"
        )

        print("🚀 吉林一号(JL1Mall) 影像服务已连接 (TMS模式适配)")

    def get_image_data(
        self, 
        location: Union[List[float], Tuple[float, float], List[float]], 
        year: int = 2024,
        zoom_level: int = 18,
        point_size: int = 2000
    ) -> np.ndarray:
        """
        核心入口：获取影像数据并返回 Numpy 数组
        """
        # 1. 选择图源
        if year >= 2024:
            template = self.url_template_2024
            print(f"🌍 使用 2024 图源 (Zoom: {zoom_level})...")
        elif year == 2023:
            template = self.url_template_2023
            print(f"📜 使用 2023 图源 (Zoom: {zoom_level})...")
        elif year == 2022:
            template = self.url_template_2022
            print(f"📜 使用 2022 图源 (Zoom: {zoom_level})...")

        # 2. 区分模式
        if len(location) == 2:
            print(f"📍 模式: 单点截取 (中心: {location})")
            img = self._process_point(location, zoom_level, point_size, template)
        elif len(location) == 4:
            print(f"🗺️ 模式: 区域拼接 (范围: {location})")
            img = self._process_bbox(location, zoom_level, template)
        else:
            raise ValueError("坐标格式错误")

        if img is None:
            return None

        print("📥 转换 NumPy 数组...")
        return np.array(img.convert('RGB'))

    def _get_tile_url(self, x_google, y_google, z, template):
        """
        URL 构造核心逻辑 (关键修改部分)
        """
        # mercantile 库返回的是 Google XYZ 标准 (原点在左上角)
        # 你的 URL 包含 {-y}，这在 OpenLayers/QGIS 中代表 TMS 标准 (原点在左下角)
        # 转换公式: y_tms = 2^z - 1 - y_google
        
        y_tms = (2 ** z) - 1 - y_google
        
        # 执行替换
        url = template.replace("{z}", str(z)) \
                      .replace("{x}", str(x_google)) \
                      .replace("{-y}", str(y_tms))
        return url

    def _process_point(self, loc, zoom, size, template):
        """处理单点"""
        lon, lat = loc
        # 1. 计算中心瓦片 (Google XYZ 坐标)
        center_tile = mercantile.tile(lon, lat, zoom)
        
        # 2. 计算缓冲区
        buffer_tiles = math.ceil(size / 256 / 2) + 1
        min_x = center_tile.x - buffer_tiles
        max_x = center_tile.x + buffer_tiles
        min_y = center_tile.y - buffer_tiles
        max_y = center_tile.y + buffer_tiles
        
        # 3. 下载拼接
        stitched_img = self._download_and_stitch(min_x, max_x, min_y, max_y, zoom, template)
        if stitched_img is None: return None
            
        # 4. 精确裁剪 (计算经纬度在图像中的像素偏移)
        # 获取中心经纬度的 Global Pixel 坐标
        n = 2.0 ** zoom
        xtile = (lon + 180.0) / 360.0 * n
        ytile = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
        
        global_px_x = xtile * 256
        global_px_y = ytile * 256
        
        # 拼接图左上角瓦片的 Global Pixel 坐标
        stitch_ul_x = min_x * 256
        stitch_ul_y = min_y * 256
        
        # 相对坐标
        center_x = global_px_x - stitch_ul_x
        center_y = global_px_y - stitch_ul_y
        
        left = int(center_x - (size / 2))
        top = int(center_y - (size / 2))
        
        return stitched_img.crop((left, top, left + size, top + size))

    def _process_bbox(self, bbox, zoom, template):
        """处理区域"""
        tiles = list(mercantile.tiles(*bbox, zoom))
        if not tiles:
            print("❌ 区域无效")
            return None
            
        xs = [t.x for t in tiles]
        ys = [t.y for t in tiles]
        
        stitched_img = self._download_and_stitch(min(xs), max(xs), min(ys), max(ys), zoom, template)
        return stitched_img

    def _download_and_stitch(self, min_x, max_x, min_y, max_y, zoom, template):
        width = (max_x - min_x + 1) * 256
        height = (max_y - min_y + 1) * 256
        result_img = Image.new('RGB', (width, height))
        
        total = (max_x - min_x + 1) * (max_y - min_y + 1)
        print(f"🔄 开始下载 {total} 张切片...")
        
        count = 0
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                # 调用修改后的 URL 生成函数
                url = self._get_tile_url(x, y, zoom, template)
                
                try:
                    resp = requests.get(url, headers=self.headers, timeout=5)
                    if resp.status_code == 200:
                        # 校验是否为图片
                        if resp.headers.get('Content-Type', '').startswith('image') or resp.content[:4] in [b'\x89PNG', b'\xff\xd8\xff\xe0']:
                            tile = Image.open(io.BytesIO(resp.content))
                            result_img.paste(tile, ((x - min_x) * 256, (y - min_y) * 256))
                            count += 1
                        else:
                            # 可能是API返回了文本报错
                            pass
                    else:
                        print(f"⚠️ {resp.status_code} at {x},{y}")
                except Exception:
                    pass
        
        if count == 0:
            print("❌ 下载失败，请检查网络或 Key 是否过期")
            return None
            
        return result_img

# --- 验证部分 ---
if __name__ == "__main__":
    downloader = JL1MallDownloader()

    # 测试点位：北京大兴机场附近
    # zoom=18 约为 0.6米分辨率
    point_loc = [116.327307,39.995698]
    
    # 获取 2024 年数据
    img = downloader.get_image_data(point_loc, year=2022, zoom_level=17, point_size=1000)

    if img is not None:
        print(f"✅ 成功! 数组形状: {img.shape}")
        
        # 简单绘图
        try:
            import matplotlib.pyplot as plt
            plt.figure(figsize=(8,8))
            plt.imshow(img)
            plt.axis('off')
            plt.title(f"JL1 2024 Data (TMS Corrected)\nLoc: {point_loc}")
            plt.show()
        except ImportError:
            pass