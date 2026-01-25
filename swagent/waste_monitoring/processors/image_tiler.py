"""
图像切割器 - 用于测试模式将大图切割成小图块
"""
import os
import asyncio
from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass

from swagent.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class TileInfo:
    """图块信息"""
    path: str           # 图块文件路径
    row: int           # 行号
    col: int           # 列号
    x: int             # 左上角x坐标
    y: int             # 左上角y坐标
    width: int         # 宽度
    height: int        # 高度


class ImageTiler:
    """图像切割器"""

    def __init__(
        self,
        tile_size: int = 512,
        overlap: int = 64,
        output_dir: Optional[str] = None
    ):
        """
        初始化切割器

        Args:
            tile_size: 切割尺寸 (正方形)
            overlap: 重叠像素
            output_dir: 输出目录
        """
        self.tile_size = tile_size
        self.overlap = overlap
        self.output_dir = output_dir
        self.stride = tile_size - overlap

    async def split(self, image_path: str, output_dir: Optional[str] = None) -> List[str]:
        """
        将大图切割成小图块

        Args:
            image_path: 大图路径
            output_dir: 输出目录 (可选，覆盖初始化设置)

        Returns:
            切割后的小图路径列表
        """
        try:
            from PIL import Image
        except ImportError:
            logger.error("PIL未安装，请运行: pip install Pillow")
            raise ImportError("Pillow is required for image tiling")

        output_dir = output_dir or self.output_dir
        if output_dir is None:
            # 默认在图片同级目录创建tiles子目录
            output_dir = str(Path(image_path).parent / "tiles")

        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"开始切割图像: {image_path}")
        logger.info(f"切割参数: size={self.tile_size}, overlap={self.overlap}")

        # 加载图像
        image = Image.open(image_path)
        width, height = image.size
        logger.info(f"原图尺寸: {width} x {height}")

        # 计算切割网格
        cols = max(1, (width - self.overlap) // self.stride)
        rows = max(1, (height - self.overlap) // self.stride)
        total = rows * cols
        logger.info(f"将切割为 {rows} 行 x {cols} 列 = {total} 个图块")

        tile_paths = []
        base_name = Path(image_path).stem

        for row in range(rows):
            for col in range(cols):
                # 计算裁剪区域
                x = col * self.stride
                y = row * self.stride

                # 确保最后一行/列使用完整的tile_size
                x2 = min(x + self.tile_size, width)
                y2 = min(y + self.tile_size, height)

                # 如果剩余区域太小，调整起始位置
                if x2 - x < self.tile_size and x > 0:
                    x = max(0, width - self.tile_size)
                    x2 = width
                if y2 - y < self.tile_size and y > 0:
                    y = max(0, height - self.tile_size)
                    y2 = height

                # 裁剪
                tile = image.crop((x, y, x2, y2))

                # 保存
                tile_name = f"{base_name}_r{row:03d}_c{col:03d}.png"
                tile_path = os.path.join(output_dir, tile_name)
                tile.save(tile_path)
                tile_paths.append(tile_path)

        logger.info(f"切割完成，共生成 {len(tile_paths)} 个图块")
        return tile_paths

    def get_tile_info(self, tile_path: str) -> Optional[TileInfo]:
        """
        从图块文件名解析位置信息

        Args:
            tile_path: 图块路径

        Returns:
            TileInfo对象，解析失败返回None
        """
        import re
        name = Path(tile_path).stem
        match = re.search(r'_r(\d+)_c(\d+)$', name)
        if not match:
            return None

        row = int(match.group(1))
        col = int(match.group(2))

        return TileInfo(
            path=tile_path,
            row=row,
            col=col,
            x=col * self.stride,
            y=row * self.stride,
            width=self.tile_size,
            height=self.tile_size
        )


async def split_image(
    image_path: str,
    tile_size: int = 512,
    overlap: int = 64,
    output_dir: Optional[str] = None
) -> List[str]:
    """
    便捷函数：将大图切割成小图块

    Args:
        image_path: 大图路径
        tile_size: 切割尺寸
        overlap: 重叠像素
        output_dir: 输出目录

    Returns:
        切割后的小图路径列表
    """
    tiler = ImageTiler(tile_size=tile_size, overlap=overlap, output_dir=output_dir)
    return await tiler.split(image_path, output_dir)
