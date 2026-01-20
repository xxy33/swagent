"""
影像切片工具
根据 GIS 坐标，调取卫星图/无人机图库
"""
from typing import List, Dict, Optional, Union, Tuple
import numpy as np
import sys
import os

from swagent.tools.base_tool import (
    BaseTool,
    ToolCategory,
    ToolParameter,
    ToolResult
)
from swagent.utils.logger import get_logger

logger = get_logger(__name__)

# 添加数据接口路径到系统路径
_data_interface_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../数据接口'))
if _data_interface_path not in sys.path:
    sys.path.insert(0, _data_interface_path)

try:
    from opts_google import GoogleEarthDownloader
    GOOGLE_AVAILABLE = True
except ImportError as e:
    GOOGLE_AVAILABLE = False
    logger.warning(f"Google Earth Downloader not available: {e}")

try:
    from opts_jilin import JL1MallDownloader
    JILIN_AVAILABLE = True
except ImportError as e:
    JILIN_AVAILABLE = False
    logger.warning(f"Jilin-1 Downloader not available: {e}")

try:
    from opts_sentinel import SentinelProcessor
    SENTINEL_AVAILABLE = True
except ImportError as e:
    SENTINEL_AVAILABLE = False
    logger.warning(f"Sentinel Processor not available: {e}")


class ImageryTool(BaseTool):
    """
    影像切片工具

    根据 GIS 坐标，调取卫星图/无人机图库
    支持三种数据源：
    1. Google Earth - 高清卫星图（静态）
    2. Jilin-1 (吉林一号) - 国产卫星图（支持多年份）
    3. Sentinel-2 - 哨兵2号卫星图（支持时间筛选和云量过滤）
    """

    def __init__(self):
        super().__init__()
        self._google = None
        self._jilin = None
        self._sentinel = None

    @property
    def name(self) -> str:
        return "imagery_query"

    @property
    def description(self) -> str:
        return "根据 GIS 坐标获取卫星影像数据，支持 Google Earth、吉林一号和 Sentinel-2 三种数据源"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.DOMAIN

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="location",
                type="array",
                description="位置坐标。点位: [lon, lat]；区域: [min_lon, min_lat, max_lon, max_lat]",
                required=True,
                items={"type": "number"}
            ),
            ToolParameter(
                name="source",
                type="string",
                description="数据源",
                required=True,
                enum=["google", "jilin", "sentinel"]
            ),
            ToolParameter(
                name="zoom_level",
                type="number",
                description="缩放级别 (仅 Google/Jilin)。18约为0.6m分辨率，19约为0.3m分辨率",
                required=False,
                default=18
            ),
            ToolParameter(
                name="point_size",
                type="number",
                description="点位模式下生成的图片像素大小 (仅 Google/Jilin)，默认 2000x2000",
                required=False,
                default=2000
            ),
            ToolParameter(
                name="year",
                type="number",
                description="年份 (仅 Jilin)。支持 2022, 2023, 2024",
                required=False,
                default=2024
            ),
            ToolParameter(
                name="date_range",
                type="array",
                description="日期范围 (仅 Sentinel)，格式: ['2023-01-01', '2023-01-31']",
                required=False,
                items={"type": "string"}
            ),
            ToolParameter(
                name="bands",
                type="array",
                description="波段 (仅 Sentinel)，默认 RGB: ['B4', 'B3', 'B2']",
                required=False,
                items={"type": "string"}
            ),
            ToolParameter(
                name="max_cloud_cover",
                type="number",
                description="最大云量百分比 (仅 Sentinel)，默认 20",
                required=False,
                default=20
            ),
            ToolParameter(
                name="return_format",
                type="string",
                description="返回格式: 'array' 返回数组形状信息，'base64' 返回 base64 编码图片，'file' 保存到本地文件",
                required=False,
                default="array",
                enum=["array", "base64", "file"]
            ),
            ToolParameter(
                name="output_path",
                type="string",
                description="保存路径（仅当 return_format='file' 时使用），支持相对路径和绝对路径",
                required=False,
                default="./imagery_output"
            ),
            ToolParameter(
                name="filename",
                type="string",
                description="文件名（可选），不指定则自动生成。支持 .png, .jpg, .tiff 格式",
                required=False,
                default=None
            )
        ]

    def get_return_description(self) -> str:
        return "返回包含影像数据的字典，包括数据源、位置、数组形状或 base64 编码的图片等信息"

    def get_examples(self) -> List[Dict]:
        return [
            {
                "input": {
                    "location": [116.4074, 39.9042],
                    "source": "google",
                    "zoom_level": 18,
                    "point_size": 2000
                },
                "output": {
                    "source": "google",
                    "location": [116.4074, 39.9042],
                    "shape": [2000, 2000, 3],
                    "mode": "point"
                }
            },
            {
                "input": {
                    "location": [116.35, 39.85, 116.45, 39.95],
                    "source": "jilin",
                    "zoom_level": 18,
                    "year": 2024
                },
                "output": {
                    "source": "jilin",
                    "location": [116.35, 39.85, 116.45, 39.95],
                    "shape": [2560, 2560, 3],
                    "mode": "bbox",
                    "year": 2024
                }
            },
            {
                "input": {
                    "location": [116.397, 39.908],
                    "source": "sentinel",
                    "date_range": ["2023-05-01", "2023-09-01"],
                    "bands": ["B4", "B3", "B2"],
                    "max_cloud_cover": 10
                },
                "output": {
                    "source": "sentinel",
                    "location": [116.397, 39.908],
                    "shape": [1000, 1000, 3],
                    "mode": "point",
                    "date_range": ["2023-05-01", "2023-09-01"]
                }
            }
        ]

    async def execute(self, **kwargs) -> ToolResult:
        """执行影像查询"""
        location = kwargs["location"]
        source = kwargs["source"]

        logger.info(f"影像查询 - 数据源: {source}, 位置: {location}")

        try:
            if source == "google":
                result = await self._query_google(location, kwargs)
            elif source == "jilin":
                result = await self._query_jilin(location, kwargs)
            elif source == "sentinel":
                result = await self._query_sentinel(location, kwargs)
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unsupported source: {source}"
                )

            logger.info(f"影像查询完成 - 数据源: {source}")

            return ToolResult(
                success=True,
                data=result,
                metadata={
                    "source": source,
                    "location": location
                }
            )

        except Exception as e:
            logger.error(f"影像查询异常: {str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                data=None,
                error=f"Imagery query error: {str(e)}"
            )

    async def _query_google(self, location: List[float], kwargs: Dict) -> Dict:
        """查询 Google Earth 影像"""
        if not GOOGLE_AVAILABLE:
            raise RuntimeError("Google Earth Downloader is not available. Please check dependencies.")

        if self._google is None:
            self._google = GoogleEarthDownloader()

        zoom_level = kwargs.get("zoom_level", 18)
        point_size = kwargs.get("point_size", 2000)
        return_format = kwargs.get("return_format", "array")
        output_path = kwargs.get("output_path", "./imagery_output")
        filename = kwargs.get("filename")

        img_array = self._google.get_image_data(
            location=location,
            zoom_level=zoom_level,
            point_size=point_size
        )

        if img_array is None:
            raise RuntimeError("Failed to retrieve Google Earth imagery")

        result = {
            "source": "google",
            "location": location,
            "shape": list(img_array.shape),
            "mode": "point" if len(location) == 2 else "bbox",
            "zoom_level": zoom_level
        }

        if return_format == "base64":
            result["image_base64"] = self._array_to_base64(img_array)
        elif return_format == "file":
            filepath = self._save_to_file(
                img_array,
                output_path=output_path,
                filename=filename,
                source="google",
                location=location
            )
            result["saved_path"] = filepath
            result["filename"] = os.path.basename(filepath)
        else:
            result["array_info"] = {
                "dtype": str(img_array.dtype),
                "min": float(np.min(img_array)),
                "max": float(np.max(img_array)),
                "mean": float(np.mean(img_array))
            }

        return result

    async def _query_jilin(self, location: List[float], kwargs: Dict) -> Dict:
        """查询吉林一号影像"""
        if not JILIN_AVAILABLE:
            raise RuntimeError("Jilin-1 Downloader is not available. Please check dependencies.")

        if self._jilin is None:
            self._jilin = JL1MallDownloader()

        zoom_level = kwargs.get("zoom_level", 18)
        point_size = kwargs.get("point_size", 2000)
        year = kwargs.get("year", 2024)
        return_format = kwargs.get("return_format", "array")
        output_path = kwargs.get("output_path", "./imagery_output")
        filename = kwargs.get("filename")

        img_array = self._jilin.get_image_data(
            location=location,
            year=year,
            zoom_level=zoom_level,
            point_size=point_size
        )

        if img_array is None:
            raise RuntimeError("Failed to retrieve Jilin-1 imagery")

        result = {
            "source": "jilin",
            "location": location,
            "shape": list(img_array.shape),
            "mode": "point" if len(location) == 2 else "bbox",
            "zoom_level": zoom_level,
            "year": year
        }

        if return_format == "base64":
            result["image_base64"] = self._array_to_base64(img_array)
        elif return_format == "file":
            filepath = self._save_to_file(
                img_array,
                output_path=output_path,
                filename=filename,
                source=f"jilin_{year}",
                location=location
            )
            result["saved_path"] = filepath
            result["filename"] = os.path.basename(filepath)
        else:
            result["array_info"] = {
                "dtype": str(img_array.dtype),
                "min": float(np.min(img_array)),
                "max": float(np.max(img_array)),
                "mean": float(np.mean(img_array))
            }

        return result

    async def _query_sentinel(self, location: List[float], kwargs: Dict) -> Dict:
        """查询 Sentinel-2 影像"""
        if not SENTINEL_AVAILABLE:
            raise RuntimeError("Sentinel Processor is not available. Please check dependencies.")

        if self._sentinel is None:
            self._sentinel = SentinelProcessor()

        date_range = kwargs.get("date_range", ["2023-01-01", "2023-12-31"])
        bands = kwargs.get("bands", ["B4", "B3", "B2"])
        max_cloud_cover = kwargs.get("max_cloud_cover", 20)
        return_format = kwargs.get("return_format", "array")
        output_path = kwargs.get("output_path", "./imagery_output")
        filename = kwargs.get("filename")

        if not isinstance(date_range, (list, tuple)) or len(date_range) != 2:
            raise ValueError("date_range must be a list/tuple of 2 date strings")

        img_array = self._sentinel.get_sentinel_data(
            location=location,
            date_range=tuple(date_range),
            bands=bands,
            max_cloud_cover=max_cloud_cover
        )

        if img_array is None:
            raise RuntimeError("Failed to retrieve Sentinel-2 imagery")

        result = {
            "source": "sentinel",
            "location": location,
            "shape": list(img_array.shape),
            "mode": "point" if len(location) == 2 else "bbox",
            "date_range": date_range,
            "bands": bands,
            "max_cloud_cover": max_cloud_cover
        }

        if return_format == "base64":
            # Sentinel 数据需要归一化
            normalized = np.clip(img_array.astype(float) / 3000.0, 0, 1)
            result["image_base64"] = self._array_to_base64((normalized * 255).astype(np.uint8))
        elif return_format == "file":
            # Sentinel 数据需要归一化后保存
            normalized = np.clip(img_array.astype(float) / 3000.0, 0, 1)
            normalized_uint8 = (normalized * 255).astype(np.uint8)

            filepath = self._save_to_file(
                normalized_uint8,
                output_path=output_path,
                filename=filename,
                source="sentinel",
                location=location
            )
            result["saved_path"] = filepath
            result["filename"] = os.path.basename(filepath)
        else:
            result["array_info"] = {
                "dtype": str(img_array.dtype),
                "min": float(np.min(img_array)),
                "max": float(np.max(img_array)),
                "mean": float(np.mean(img_array))
            }

        return result

    def _array_to_base64(self, img_array: np.ndarray) -> str:
        """将 numpy 数组转换为 base64 编码的图片"""
        from PIL import Image
        import io
        import base64

        # 确保是 RGB 格式
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            img = Image.fromarray(img_array.astype(np.uint8), mode='RGB')
        else:
            img = Image.fromarray(img_array.astype(np.uint8))

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        return img_base64

    def _save_to_file(
        self,
        img_array: np.ndarray,
        output_path: str,
        filename: Optional[str] = None,
        source: str = "imagery",
        location: List[float] = None
    ) -> str:
        """
        将 numpy 数组保存到本地文件

        参数:
            img_array: 图像数组
            output_path: 输出目录路径
            filename: 文件名（可选）
            source: 数据源名称（用于自动生成文件名）
            location: 坐标信息（用于自动生成文件名）

        返回:
            保存的文件完整路径
        """
        from PIL import Image
        from datetime import datetime

        # 创建输出目录
        os.makedirs(output_path, exist_ok=True)

        # 生成文件名
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if location and len(location) >= 2:
                loc_str = f"{location[0]:.4f}_{location[1]:.4f}"
                filename = f"{source}_{loc_str}_{timestamp}.png"
            else:
                filename = f"{source}_{timestamp}.png"

        # 确保文件名有扩展名
        if not any(filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.tiff', '.tif']):
            filename += '.png'

        # 完整路径
        filepath = os.path.join(output_path, filename)

        # 转换为 PIL Image 并保存
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            img = Image.fromarray(img_array.astype(np.uint8), mode='RGB')
        else:
            img = Image.fromarray(img_array.astype(np.uint8))

        # 根据文件扩展名保存
        img.save(filepath)

        logger.info(f"影像已保存到: {filepath}")

        return os.path.abspath(filepath)
