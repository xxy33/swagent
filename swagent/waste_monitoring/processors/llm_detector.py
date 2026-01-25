"""
大模型检测器 - 调用视觉语言模型进行垃圾堆存检测
输出 JSON 格式：reasoning, label, description, boundingbox
"""
import base64
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from swagent.utils.logger import get_logger

logger = get_logger(__name__)

# System prompt 文件路径
SYSTEM_PROMPT_PATH = Path(__file__).parent.parent.parent.parent / "scripts" / "prompt_template" / "sw_check_sp.md"


@dataclass
class LLMDetectorConfig:
    """大模型检测器配置"""
    base_url: str = None
    api_key: str = None
    model: str = None
    max_retries: int = 3


class LLMDetector:
    """大模型垃圾检测器"""

    def __init__(
        self,
        config: LLMDetectorConfig = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_retries: int = 3
    ):
        """
        初始化检测器

        Args:
            config: 检测器配置对象
            base_url: API基础地址
            api_key: API密钥
            model: 模型名称
            max_retries: 最大重试次数
        """
        self.config = config or LLMDetectorConfig(
            base_url=base_url,
            api_key=api_key,
            model=model,
            max_retries=max_retries
        )
        self._client = None
        self._client_initialized = False
        self._system_prompt = None

    def _load_system_prompt(self) -> str:
        """加载 system prompt"""
        if self._system_prompt is None:
            if SYSTEM_PROMPT_PATH.exists():
                self._system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
                logger.debug(f"已加载 system prompt: {SYSTEM_PROMPT_PATH}")
            else:
                logger.warning(f"System prompt 文件不存在: {SYSTEM_PROMPT_PATH}")
                self._system_prompt = "You are an AI that detects waste in satellite imagery. Output JSON with: reasoning, label (1=waste, 0=clean), description, boundingbox."
        return self._system_prompt

    async def _get_client(self):
        """获取 LLM 客户端"""
        if self._client is None and not self._client_initialized:
            from swagent.llm.openai_client import OpenAIClient
            from swagent.llm.base_llm import LLMConfig

            if self.config.base_url and self.config.api_key:
                llm_config = LLMConfig(
                    provider="openai",
                    base_url=self.config.base_url,
                    api_key=self.config.api_key,
                    model=self.config.model or "gpt-4o-mini"
                )
                self._client = OpenAIClient(config=llm_config)
            else:
                # 使用默认配置
                self._client = OpenAIClient.from_config_file()

            self._client_initialized = True

        return self._client

    async def detect(self, image_path: str) -> Dict[str, Any]:
        """
        对图片进行垃圾堆存检测

        Args:
            image_path: 图片路径

        Returns:
            检测结果字典，包含 reasoning, label, description, boundingbox
        """
        logger.debug(f"LLM 检测: {Path(image_path).name}")

        client = await self._get_client()
        if client is None:
            logger.error("LLM 客户端未初始化，请检查 API 配置")
            return self._error_result("LLM client not initialized")

        # 读取并编码图片
        image_base64 = self._encode_image(image_path)
        system_prompt = self._load_system_prompt()

        # 重试机制
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                result = await self._call_llm(client, system_prompt, image_base64)
                if result is not None:
                    logger.debug(f"LLM 检测成功: label={result.get('label')}")
                    return result
            except Exception as e:
                last_error = str(e)
                logger.warning(f"LLM 检测第 {attempt + 1} 次失败: {e}")

        # 所有重试都失败
        logger.error(f"LLM 检测失败，已重试 {self.config.max_retries} 次")
        return self._error_result(f"Failed after {self.config.max_retries} attempts: {last_error}")

    async def _call_llm(
        self,
        client,
        system_prompt: str,
        image_base64: str
    ) -> Optional[Dict[str, Any]]:
        """调用 LLM 并解析响应"""
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]

        response = await client.chat(messages, temperature=0.1, max_tokens=2000)
        content = response.content

        # 解析 JSON 响应
        result = self._parse_json_response(content)
        return result

    def _encode_image(self, image_path: str) -> str:
        """将图片编码为 base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    def _parse_json_response(self, content: str) -> Optional[Dict[str, Any]]:
        """
        解析 LLM 的 JSON 响应

        处理情况：
        1. 纯 JSON 字符串
        2. ```json ... ``` 包裹的 JSON
        3. <think>...</think> 后跟 JSON
        4. <answer>...</answer> 格式
        5. 其他格式（尝试提取）
        """
        original_content = content
        content = content.strip()

        # 处理 <think>...</think> 格式 - 提取 </think> 后的内容
        think_match = re.search(r'</think>\s*(.*)', content, re.DOTALL)
        if think_match:
            content = think_match.group(1).strip()

        # 尝试直接解析 JSON
        try:
            result = json.loads(content)
            return self._validate_result(result)
        except json.JSONDecodeError:
            pass

        # 处理 ```json ... ``` 格式
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if json_match:
            try:
                result = json.loads(json_match.group(1))
                return self._validate_result(result)
            except json.JSONDecodeError:
                pass

        # 尝试提取 {...} 格式
        brace_match = re.search(r'\{[\s\S]*\}', content)
        if brace_match:
            try:
                result = json.loads(brace_match.group())
                return self._validate_result(result)
            except json.JSONDecodeError:
                pass

        # 处理 <answer>0</answer> 或 <answer>1</answer> 格式
        answer_match = re.search(r'<answer>\s*([01])\s*</answer>', original_content)
        if answer_match:
            label = int(answer_match.group(1))
            # 尝试从 <think> 中提取描述
            think_content = ""
            think_match = re.search(r'<think>(.*?)</think>', original_content, re.DOTALL)
            if think_match:
                think_content = think_match.group(1).strip()[:500]

            return {
                "reasoning": think_content or f"Model returned label {label}",
                "label": label,
                "description": think_content[:200] if think_content else ("检测到垃圾堆存" if label == 1 else "未检测到垃圾"),
                "boundingbox": [],
                "error": False
            }

        logger.warning(f"无法解析 JSON 响应: {content[:200]}...")
        return None

    def _validate_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """验证并规范化结果"""
        # 确保必要字段存在
        validated = {
            "reasoning": result.get("reasoning", ""),
            "label": int(result.get("label", 0)),
            "description": result.get("description", ""),
            "boundingbox": result.get("boundingbox", []),
            "error": False
        }

        # 确保 label 是 0 或 1
        if validated["label"] not in [0, 1]:
            validated["label"] = 0

        # 确保 boundingbox 是列表格式 [[ymin, xmin, ymax, xmax], ...]
        bbox = validated["boundingbox"]
        if not isinstance(bbox, list):
            validated["boundingbox"] = []
        elif bbox and not isinstance(bbox[0], list):
            # 单个 bbox 转换为列表格式
            validated["boundingbox"] = [bbox]

        return validated

    def _error_result(self, error_msg: str) -> Dict[str, Any]:
        """生成错误结果"""
        return {
            "reasoning": f"ERROR: {error_msg}",
            "label": -1,
            "description": "Detection failed",
            "boundingbox": [],
            "error": True
        }


# 全局检测器实例
_global_detector: Optional[LLMDetector] = None


async def call_llm_api(
    image_path: str,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    便捷函数：调用大模型 API 进行垃圾检测

    Args:
        image_path: 图片路径
        base_url: API 基础地址
        api_key: API 密钥
        model: 模型名称
        max_retries: 最大重试次数

    Returns:
        检测结果字典，包含:
        - reasoning: 推理过程
        - label: 1=有垃圾, 0=无垃圾, -1=错误
        - description: 描述
        - boundingbox: [[ymin, xmin, ymax, xmax], ...]
        - error: 是否出错
    """
    global _global_detector

    # 如果有自定义配置，创建新的检测器
    if any([base_url, api_key, model]):
        detector = LLMDetector(
            base_url=base_url,
            api_key=api_key,
            model=model,
            max_retries=max_retries
        )
    else:
        # 复用全局检测器
        if _global_detector is None:
            _global_detector = LLMDetector(max_retries=max_retries)
        detector = _global_detector

    return await detector.detect(image_path)


def reset_detector():
    """重置全局检测器"""
    global _global_detector
    _global_detector = None
