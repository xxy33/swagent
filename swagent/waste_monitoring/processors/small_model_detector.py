"""
小模型图像处理器 - 对检测到垃圾的图像进行可视化处理
输入: torch.Tensor (CHW) + boundingbox
输出: numpy.ndarray (CHW) - 处理后的图像
"""
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

from swagent.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SmallModelConfig:
    """小模型配置"""
    base_url: str = None
    api_key: str = None
    model: str = None


class SmallModelProcessor:
    """小模型图像处理器"""

    def __init__(
        self,
        config: SmallModelConfig = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        初始化处理器

        Args:
            config: 配置对象
            base_url: API基础地址
            api_key: API密钥
            model: 模型名称
        """
        self.config = config or SmallModelConfig(
            base_url=base_url,
            api_key=api_key,
            model=model
        )
        self._client = None
        self._client_initialized = False

    async def _get_client(self):
        """获取API客户端"""
        if self._client is None and not self._client_initialized:
            if self.config.base_url:
                # SAM2 API 使用 HTTP 请求，不需要特殊客户端
                # 返回一个标记表示使用 API
                logger.info(f"小模型 API 配置: {self.config.base_url}")
                self._client = "sam2_api"  # 标记使用 API
            self._client_initialized = True
        return self._client

    async def process(
        self,
        image_tensor,  # torch.Tensor CHW format
        boundingboxes: List[List[float]],  # [[ymin, xmin, ymax, xmax], ...]
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理图像并标注 bounding box

        Args:
            image_tensor: torch.Tensor, CHW 格式
            boundingboxes: 边界框列表，归一化坐标 [[ymin, xmin, ymax, xmax], ...]
            output_path: 输出图像路径（可选）

        Returns:
            处理结果字典，包含:
            - processed_image: numpy.ndarray CHW 格式
            - output_path: 保存路径（如果指定）
            - success: 是否成功
        """
        try:
            import torch

            # 确保输入是 tensor
            if not isinstance(image_tensor, torch.Tensor):
                logger.error("输入必须是 torch.Tensor")
                return {"success": False, "error": "Input must be torch.Tensor"}

            # 获取图像尺寸 (C, H, W)
            c, h, w = image_tensor.shape

            # 转换为 numpy (CHW -> HWC for processing)
            image_np = image_tensor.cpu().numpy()
            image_hwc = np.transpose(image_np, (1, 2, 0))  # CHW -> HWC

            # 归一化到 0-255
            if image_hwc.max() <= 1.0:
                image_hwc = (image_hwc * 255).astype(np.uint8)
            else:
                image_hwc = image_hwc.astype(np.uint8)

            # 调用小模型 API 或本地处理
            client = await self._get_client()

            if client is not None:
                # TODO: 调用远程 API
                processed_hwc = await self._call_api(client, image_hwc, boundingboxes)
            else:
                # 本地处理：绘制 bounding box
                processed_hwc = self._draw_bboxes(image_hwc.copy(), boundingboxes)

            # 转换回 CHW 格式
            processed_chw = np.transpose(processed_hwc, (2, 0, 1))  # HWC -> CHW

            result = {
                "processed_image": processed_chw,
                "success": True,
                "bbox_count": len(boundingboxes)
            }

            # 保存图像
            if output_path:
                self._save_image(processed_hwc, output_path)
                result["output_path"] = output_path
                logger.debug(f"处理后图像已保存: {output_path}")

            return result

        except Exception as e:
            logger.error(f"图像处理失败: {e}")
            return {"success": False, "error": str(e)}

    async def _call_api(
        self,
        client,
        image_hwc: np.ndarray,
        boundingboxes: List[List[float]]
    ) -> np.ndarray:
        """
        调用小模型 API (SAM2)

        Args:
            client: API 客户端
            image_hwc: HWC 格式图像
            boundingboxes: 边界框列表 [[ymin, xmin, ymax, xmax], ...]

        Returns:
            处理后的 HWC 格式图像
        """
        try:
            import requests
            import json
            import cv2
            import tempfile

            # 转换 boundingboxes 格式: [ymin, xmin, ymax, xmax] -> [xmin, ymin, xmax, ymax]
            boxes_relative = []
            for bbox in boundingboxes:
                if len(bbox) == 4:
                    ymin, xmin, ymax, xmax = bbox
                    boxes_relative.append([xmin, ymin, xmax, ymax])

            if not boxes_relative:
                logger.warning("没有有效的边界框，返回原图")
                return image_hwc

            # 保存临时图像
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                tmp_path = tmp_file.name
                cv2.imwrite(tmp_path, cv2.cvtColor(image_hwc, cv2.COLOR_RGB2BGR))

            # 构建请求
            url = f"{self.config.base_url}/sam2_large"
            payload = {
                "boxes": json.dumps(boxes_relative)
            }
            files = {
                "file": open(tmp_path, "rb")
            }

            logger.debug(f"调用 SAM2 API: {url}, boxes: {boxes_relative}")

            # 发送请求
            response = requests.post(url, data=payload, files=files, timeout=60)
            files["file"].close()

            # 清理临时文件
            import os
            os.unlink(tmp_path)

            if response.status_code == 200:
                # 解码mask
                image_bytes = np.frombuffer(response.content, np.uint8)
                mask = cv2.imdecode(image_bytes, cv2.IMREAD_GRAYSCALE)

                # 确保mask和原图尺寸一致
                if mask.shape[:2] != image_hwc.shape[:2]:
                    mask = cv2.resize(mask, (image_hwc.shape[1], image_hwc.shape[0]))

                # 综合效果：半透明填充 + 轮廓线
                result = image_hwc.copy()

                # 半透明绿色填充
                colored_mask = np.zeros_like(result)
                colored_mask[mask > 127] = (0, 255, 0)  # 绿色
                result = cv2.addWeighted(result, 1, colored_mask, 0.3, 0)

                # 黄色轮廓线
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                cv2.drawContours(result, contours, -1, (0, 255, 255), 2)

                logger.info(f"SAM2 API 调用成功，处理了 {len(boxes_relative)} 个区域")
                return result
            else:
                logger.error(f"SAM2 API 调用失败: {response.status_code}, {response.text}")
                # 降级到本地绘制
                return self._draw_bboxes(image_hwc, boundingboxes)

        except Exception as e:
            logger.error(f"SAM2 API 调用异常: {e}")
            # 降级到本地绘制
            return self._draw_bboxes(image_hwc, boundingboxes)

    def _draw_bboxes(
        self,
        image: np.ndarray,
        boundingboxes: List[List[float]],
        color: tuple = (255, 0, 0),  # Red
        thickness: int = 3
    ) -> np.ndarray:
        """
        在图像上绘制 bounding box

        Args:
            image: HWC 格式图像
            boundingboxes: 归一化坐标 [[ymin, xmin, ymax, xmax], ...]
            color: 框颜色 (R, G, B)
            thickness: 线条粗细

        Returns:
            绘制后的图像
        """
        h, w = image.shape[:2]

        for bbox in boundingboxes:
            if len(bbox) != 4:
                continue

            ymin, xmin, ymax, xmax = bbox

            # 转换为像素坐标
            x1 = int(xmin * w)
            y1 = int(ymin * h)
            x2 = int(xmax * w)
            y2 = int(ymax * h)

            # 确保坐标在图像范围内
            x1 = max(0, min(w - 1, x1))
            y1 = max(0, min(h - 1, y1))
            x2 = max(0, min(w - 1, x2))
            y2 = max(0, min(h - 1, y2))

            # 绘制矩形框
            # 上边
            image[y1:y1+thickness, x1:x2] = color
            # 下边
            image[y2-thickness:y2, x1:x2] = color
            # 左边
            image[y1:y2, x1:x1+thickness] = color
            # 右边
            image[y1:y2, x2-thickness:x2] = color

        return image

    def _save_image(self, image_hwc: np.ndarray, output_path: str):
        """保存图像为 PNG"""
        try:
            from PIL import Image
            img = Image.fromarray(image_hwc)
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            img.save(output_path, 'PNG')
        except ImportError:
            # 使用 matplotlib 作为备选
            import matplotlib.pyplot as plt
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            plt.imsave(output_path, image_hwc)


async def process_image_with_small_model(
    image_path: str,
    boundingboxes: List[List[float]],
    output_dir: str,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> Dict[str, Any]:
    """
    便捷函数：使用小模型处理图像

    Args:
        image_path: 输入图像路径
        boundingboxes: 边界框列表
        output_dir: 输出目录
        base_url: API 地址
        api_key: API 密钥
        model: 模型名称

    Returns:
        处理结果
    """
    import torch
    from PIL import Image

    # 读取图像
    img = Image.open(image_path).convert('RGB')
    img_np = np.array(img)

    # 转换为 CHW tensor
    img_tensor = torch.from_numpy(img_np).permute(2, 0, 1).float() / 255.0

    # 生成输出路径
    tile_id = Path(image_path).stem
    output_path = str(Path(output_dir) / "processed" / f"{tile_id}_processed.png")

    # 创建处理器
    processor = SmallModelProcessor(
        base_url=base_url,
        api_key=api_key,
        model=model
    )

    # 处理图像
    result = await processor.process(
        image_tensor=img_tensor,
        boundingboxes=boundingboxes,
        output_path=output_path
    )

    return result


# 保持向后兼容的函数名
async def call_small_model_api(
    image_path: str,
    boundingboxes: List[List[float]] = None,
    output_dir: str = "./output",
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None
) -> Dict[str, Any]:
    """
    向后兼容的 API 调用函数

    Args:
        image_path: 图像路径
        boundingboxes: 边界框列表
        output_dir: 输出目录
        base_url: API 地址
        api_key: API 密钥
        model: 模型名称

    Returns:
        处理结果
    """
    if boundingboxes is None:
        boundingboxes = []

    return await process_image_with_small_model(
        image_path=image_path,
        boundingboxes=boundingboxes,
        output_dir=output_dir,
        base_url=base_url,
        api_key=api_key,
        model=model
    )


def reset_processor():
    """重置处理器（预留接口）"""
    pass
