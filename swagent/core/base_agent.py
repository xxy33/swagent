"""
Agent基类
定义Agent的核心接口和通用功能
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import uuid

from swagent.core.message import Message, MessageType
from swagent.core.context import ContextManager, ContextScope
from swagent.llm.base_llm import BaseLLM, LLMConfig
from swagent.llm.openai_client import OpenAIClient
from swagent.utils.logger import get_logger
from swagent.utils.config import get_config


logger = get_logger(__name__)


class AgentState(Enum):
    """Agent状态"""
    IDLE = "idle"               # 空闲
    THINKING = "thinking"       # 思考中
    ACTING = "acting"          # 执行中
    WAITING = "waiting"        # 等待中
    ERROR = "error"            # 错误
    STOPPED = "stopped"        # 已停止


@dataclass
class AgentConfig:
    """Agent配置"""
    name: str
    role: str
    description: str = ""
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4096
    system_prompt: Optional[str] = None
    max_iterations: int = 10
    enable_memory: bool = True
    memory_window: int = 20

    # LLM配置
    llm_config: Optional[LLMConfig] = None

    # 额外配置
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """Agent基类"""

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        初始化Agent

        Args:
            config: Agent配置
        """
        if config is None:
            config = self._load_default_config()

        self.config = config
        self.agent_id = str(uuid.uuid4())
        self.state = AgentState.IDLE

        # 初始化LLM
        self.llm = self._init_llm()

        # 初始化上下文管理器
        self.context_manager = ContextManager(max_history=config.memory_window)

        # 创建初始上下文
        self.context_manager.create_context(
            context_id=self.agent_id,
            scope=ContextScope.AGENT,
            initial_data={
                "agent_name": self.config.name,
                "agent_role": self.config.role
            }
        )

        # 通信器（由Orchestrator设置）
        self.communicator: Optional['AgentCommunicator'] = None

        logger.info(f"Agent初始化成功 - ID: {self.agent_id}, 名称: {self.config.name}, 角色: {self.config.role}")

    def _load_default_config(self) -> AgentConfig:
        """加载默认配置"""
        cfg = get_config()
        agent_config = cfg.get('agents', {})

        return AgentConfig(
            name="BaseAgent",
            role="通用Agent",
            description="基础Agent",
            temperature=agent_config.get('default_temperature', 0.7),
            max_tokens=agent_config.get('default_max_tokens', 4096),
            memory_window=agent_config.get('memory_window_size', 20)
        )

    def _init_llm(self) -> BaseLLM:
        """初始化LLM客户端"""
        if self.config.llm_config:
            return OpenAIClient(self.config.llm_config)
        else:
            # 从配置文件加载
            return OpenAIClient.from_config_file()

    @property
    def system_prompt(self) -> str:
        """获取系统提示"""
        if self.config.system_prompt:
            return self.config.system_prompt

        return f"""你是 {self.config.name}，一个{self.config.role}。

角色描述：{self.config.description}

请根据你的角色定位，专业地完成用户的请求。"""

    async def run(self, message: Message) -> Message:
        """
        运行Agent（主入口）

        Args:
            message: 输入消息

        Returns:
            响应消息
        """
        try:
            logger.info(f"Agent开始处理消息 - 发送者: {message.sender}, 内容长度: {len(message.content)}")

            # 更新状态
            self.state = AgentState.THINKING

            # 添加消息到历史
            if self.config.enable_memory:
                self.context_manager.add_message(message)

            # 处理消息
            response = await self.process(message)

            # 添加响应到历史
            if self.config.enable_memory:
                self.context_manager.add_message(response)

            # 更新状态
            self.state = AgentState.IDLE

            logger.info(f"Agent处理完成 - 响应长度: {len(response.content)}")

            return response

        except Exception as e:
            logger.error(f"Agent处理出错: {str(e)}", exc_info=True)
            self.state = AgentState.ERROR

            # 返回错误消息
            return Message(
                sender=self.agent_id,
                sender_name=self.config.name,
                receiver=message.sender,
                receiver_name=message.sender_name,
                content=f"处理出错: {str(e)}",
                msg_type=MessageType.ERROR
            )

    @abstractmethod
    async def process(self, message: Message) -> Message:
        """
        处理消息（子类必须实现）

        Args:
            message: 输入消息

        Returns:
            响应消息
        """
        pass

    async def chat(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        use_history: bool = True
    ) -> str:
        """
        简单对话接口

        Args:
            user_message: 用户消息
            system_prompt: 系统提示（覆盖默认）
            use_history: 是否使用历史对话

        Returns:
            LLM响应内容
        """
        messages = []

        # 添加系统提示
        prompt = system_prompt or self.system_prompt
        if prompt:
            messages.append({"role": "system", "content": prompt})

        # 添加历史对话
        if use_history and self.config.enable_memory:
            history = self.context_manager.get_conversation_history(
                limit=self.config.memory_window - 2  # 留出系统提示和当前消息的空间
            )
            # 过滤掉系统消息，避免重复
            history = [m for m in history if m.get("role") != "system"]
            messages.extend(history)

        # 添加当前消息
        messages.append({"role": "user", "content": user_message})

        # 调用LLM
        response = await self.llm.chat(
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens
        )

        return response.content

    def get_state(self) -> Dict[str, Any]:
        """
        获取Agent状态

        Returns:
            状态信息
        """
        return {
            "agent_id": self.agent_id,
            "name": self.config.name,
            "role": self.config.role,
            "state": self.state.value,
            "model": self.llm.model_name,
            "context_summary": self.context_manager.get_summary()
        }

    def reset(self):
        """重置Agent状态"""
        self.state = AgentState.IDLE
        self.context_manager.reset()
        logger.info(f"Agent已重置 - {self.config.name}")

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.config.name}, role={self.config.role}, state={self.state.value})>"
