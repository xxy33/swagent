"""
OpenAI兼容客户端
支持OpenAI API和其他兼容OpenAI格式的API（可自定义base_url）
"""
import asyncio
from typing import List, Dict, Any, Optional, AsyncIterator
from openai import AsyncOpenAI, OpenAIError
from swagent.llm.base_llm import BaseLLM, LLMConfig, LLMResponse
from swagent.utils.logger import get_logger


logger = get_logger(__name__)


class OpenAIClient(BaseLLM):
    """OpenAI兼容客户端"""

    def __init__(self, config: Optional[LLMConfig] = None):
        """
        初始化OpenAI客户端

        Args:
            config: LLM配置，如果为None则从全局配置读取
        """
        if config is None:
            config = self._load_config_from_file()

        super().__init__(config)

        # 初始化OpenAI客户端
        self.client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout,
            max_retries=self.config.max_retries
        )

        logger.info(f"OpenAI客户端初始化成功 - 模型: {self.config.model}, Base URL: {self.config.base_url}")

    @staticmethod
    def _load_config_from_file() -> LLMConfig:
        """从配置文件加载配置"""
        from swagent.utils.config import get_config

        cfg = get_config()
        provider = cfg.get('llm.default_provider', 'openai')
        llm_config = cfg.get_llm_config(provider)

        return LLMConfig(
            provider=provider,
            model=llm_config.get('default_model', 'gpt-4'),
            api_key=llm_config.get('api_key'),
            base_url=llm_config.get('base_url', 'https://api.openai.com/v1'),
            timeout=llm_config.get('timeout', 60),
            max_retries=llm_config.get('max_retries', 3)
        )

    def _validate_config(self):
        """验证配置"""
        super()._validate_config()

        if not self.config.api_key:
            logger.warning("API密钥未设置，某些功能可能无法使用")

        if not self.config.base_url:
            self.config.base_url = "https://api.openai.com/v1"

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        聊天接口

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 额外参数

        Returns:
            LLMResponse对象
        """
        try:
            # 合并配置
            params = {
                "model": self.config.model,
                "messages": messages,
                "temperature": temperature or self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens,
                "top_p": self.config.top_p,
                **self.config.extra_params,
                **kwargs
            }

            logger.debug(f"发送请求到LLM - 模型: {params['model']}, 消息数: {len(messages)}")

            # 调用API
            response = await self.client.chat.completions.create(**params)

            # 解析响应
            content = response.choices[0].message.content or ""
            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            }

            logger.debug(f"收到LLM响应 - Token使用: {usage['total_tokens']}")

            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=response.choices[0].finish_reason,
                raw_response=response
            )

        except OpenAIError as e:
            logger.error(f"OpenAI API错误: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"未知错误: {str(e)}")
            raise

    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        流式聊天接口

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 额外参数

        Yields:
            文本片段
        """
        try:
            # 合并配置
            params = {
                "model": self.config.model,
                "messages": messages,
                "temperature": temperature or self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens,
                "top_p": self.config.top_p,
                "stream": True,
                **self.config.extra_params,
                **kwargs
            }

            logger.debug(f"发送流式请求到LLM - 模型: {params['model']}")

            # 调用API
            stream = await self.client.chat.completions.create(**params)

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except OpenAIError as e:
            logger.error(f"OpenAI API流式错误: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"未知流式错误: {str(e)}")
            raise

    async def count_tokens(self, text: str) -> int:
        """
        估算token数（简单方法）

        Args:
            text: 文本内容

        Returns:
            大致的token数
        """
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(self.config.model)
            return len(encoding.encode(text))
        except Exception:
            # 如果tiktoken不可用，使用简单估算
            return len(text) // 4

    @classmethod
    def from_config_file(cls, provider: Optional[str] = None) -> 'OpenAIClient':
        """
        从配置文件创建客户端

        Args:
            provider: 提供商名称，None表示使用默认

        Returns:
            OpenAIClient实例
        """
        from swagent.utils.config import get_config

        cfg = get_config()

        if provider is None:
            provider = cfg.get('llm.default_provider', 'openai')

        llm_config = cfg.get_llm_config(provider)

        config = LLMConfig(
            provider=provider,
            model=llm_config.get('default_model', 'gpt-4'),
            api_key=llm_config.get('api_key'),
            base_url=llm_config.get('base_url', 'https://api.openai.com/v1'),
            timeout=llm_config.get('timeout', 60),
            max_retries=llm_config.get('max_retries', 3)
        )

        return cls(config)

    @classmethod
    def create(
        cls,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4",
        **kwargs
    ) -> 'OpenAIClient':
        """
        快速创建客户端

        Args:
            api_key: API密钥
            base_url: API地址
            model: 模型名称
            **kwargs: 其他配置参数

        Returns:
            OpenAIClient实例
        """
        config = LLMConfig(
            provider="openai",
            model=model,
            api_key=api_key,
            base_url=base_url,
            **kwargs
        )

        return cls(config)

    async def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        tool_choice: str = "auto",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> LLMResponse:
        """
        带工具调用的聊天接口（支持Function Calling）

        Args:
            messages: 消息列表
            tools: 工具定义列表（OpenAI Function格式）
            tool_choice: 工具选择策略 ("auto", "none", 或具体工具名)
            temperature: 温度参数
            max_tokens: 最大token数
            **kwargs: 额外参数

        Returns:
            LLMResponse对象（可能包含tool_calls）
        """
        try:
            # 合并配置
            params = {
                "model": self.config.model,
                "messages": messages,
                "tools": tools,
                "tool_choice": tool_choice,
                "temperature": temperature or self.config.temperature,
                "max_tokens": max_tokens or self.config.max_tokens,
                "top_p": self.config.top_p,
                **self.config.extra_params,
                **kwargs
            }

            logger.debug(f"发送工具请求到LLM - 模型: {params['model']}, 工具数: {len(tools)}")

            # 调用API
            response = await self.client.chat.completions.create(**params)

            # 解析响应
            message = response.choices[0].message
            content = message.content or ""

            # 提取tool_calls
            tool_calls = None
            if hasattr(message, 'tool_calls') and message.tool_calls:
                tool_calls = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]

            usage = {
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            }

            logger.debug(f"收到LLM响应 - Tool calls: {len(tool_calls) if tool_calls else 0}")

            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                finish_reason=response.choices[0].finish_reason,
                raw_response=response,
                tool_calls=tool_calls  # 添加tool_calls到响应
            )

        except OpenAIError as e:
            logger.error(f"OpenAI API错误: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"未知错误: {str(e)}")
            raise
