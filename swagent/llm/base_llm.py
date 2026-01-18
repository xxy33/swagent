"""
LLM基类
定义LLM接口的抽象基类
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, AsyncIterator
from enum import Enum


class ModelProvider(Enum):
    """模型提供商"""
    OPENAI = "openai"
    LOCAL = "local"
    AZURE = "azure"


@dataclass
class LLMConfig:
    """LLM配置"""
    provider: str = "openai"
    model: str = "gpt-4"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    timeout: int = 60
    max_retries: int = 3
    stream: bool = False

    # 额外参数
    extra_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    finish_reason: Optional[str] = None
    raw_response: Optional[Any] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None  # Function Calling结果

    @property
    def prompt_tokens(self) -> int:
        """输入token数"""
        return self.usage.get('prompt_tokens', 0)

    @property
    def completion_tokens(self) -> int:
        """输出token数"""
        return self.usage.get('completion_tokens', 0)

    @property
    def total_tokens(self) -> int:
        """总token数"""
        return self.usage.get('total_tokens', 0)

    @property
    def has_tool_calls(self) -> bool:
        """是否包含工具调用"""
        return self.tool_calls is not None and len(self.tool_calls) > 0


class BaseLLM(ABC):
    """LLM基类"""

    def __init__(self, config: LLMConfig):
        """
        初始化LLM

        Args:
            config: LLM配置
        """
        self.config = config
        self._validate_config()

    def _validate_config(self):
        """验证配置"""
        if not self.config.model:
            raise ValueError("Model name is required")

    @abstractmethod
    async def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """
        聊天接口

        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}]
            **kwargs: 额外参数

        Returns:
            LLMResponse对象
        """
        pass

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> AsyncIterator[str]:
        """
        流式聊天接口

        Args:
            messages: 消息列表
            **kwargs: 额外参数

        Yields:
            文本片段
        """
        pass

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        文本生成接口（简化版）

        Args:
            prompt: 用户提示
            system_prompt: 系统提示
            **kwargs: 额外参数

        Returns:
            LLMResponse对象
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        return await self.chat(messages, **kwargs)

    def format_messages(
        self,
        prompt: str,
        history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        格式化消息

        Args:
            prompt: 当前提示
            history: 历史对话
            system_prompt: 系统提示

        Returns:
            格式化后的消息列表
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": prompt})

        return messages

    @property
    def model_name(self) -> str:
        """获取模型名称"""
        return self.config.model

    @property
    def provider(self) -> str:
        """获取提供商"""
        return self.config.provider
