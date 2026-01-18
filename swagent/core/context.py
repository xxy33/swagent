"""
上下文管理模块
负责管理Agent执行过程中的上下文信息
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
from swagent.core.message import Message


class ContextScope(Enum):
    """上下文范围"""
    SESSION = "session"      # 会话级别
    TASK = "task"           # 任务级别
    AGENT = "agent"         # Agent级别
    GLOBAL = "global"       # 全局级别


@dataclass
class ExecutionContext:
    """执行上下文"""
    id: str
    scope: ContextScope
    data: Dict[str, Any] = field(default_factory=dict)
    parent_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文数据"""
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        """设置上下文数据"""
        self.data[key] = value
        self.updated_at = datetime.now()

    def update(self, data: Dict[str, Any]):
        """批量更新上下文数据"""
        self.data.update(data)
        self.updated_at = datetime.now()


class ContextManager:
    """上下文管理器"""

    def __init__(self, max_history: int = 20):
        """
        初始化上下文管理器

        Args:
            max_history: 最大历史消息数
        """
        self.max_history = max_history
        self.contexts: Dict[str, ExecutionContext] = {}
        self.message_history: List[Message] = []
        self.current_context_id: Optional[str] = None

    def create_context(
        self,
        context_id: str,
        scope: ContextScope = ContextScope.SESSION,
        parent_id: Optional[str] = None,
        initial_data: Optional[Dict[str, Any]] = None
    ) -> ExecutionContext:
        """
        创建新的执行上下文

        Args:
            context_id: 上下文ID
            scope: 上下文范围
            parent_id: 父上下文ID
            initial_data: 初始数据

        Returns:
            ExecutionContext对象
        """
        context = ExecutionContext(
            id=context_id,
            scope=scope,
            parent_id=parent_id,
            data=initial_data or {}
        )
        self.contexts[context_id] = context
        self.current_context_id = context_id
        return context

    def get_context(self, context_id: Optional[str] = None) -> Optional[ExecutionContext]:
        """
        获取上下文

        Args:
            context_id: 上下文ID，None表示获取当前上下文

        Returns:
            ExecutionContext对象或None
        """
        if context_id is None:
            context_id = self.current_context_id

        return self.contexts.get(context_id) if context_id else None

    def set_current_context(self, context_id: str):
        """设置当前上下文"""
        if context_id in self.contexts:
            self.current_context_id = context_id
        else:
            raise ValueError(f"Context {context_id} does not exist")

    def add_message(self, message: Message):
        """
        添加消息到历史

        Args:
            message: 消息对象
        """
        self.message_history.append(message)

        # 限制历史长度
        if len(self.message_history) > self.max_history:
            self.message_history = self.message_history[-self.max_history:]

    def get_message_history(
        self,
        limit: Optional[int] = None,
        filter_type: Optional[str] = None
    ) -> List[Message]:
        """
        获取消息历史

        Args:
            limit: 限制数量
            filter_type: 过滤消息类型

        Returns:
            消息列表
        """
        messages = self.message_history

        if filter_type:
            messages = [m for m in messages if m.msg_type.value == filter_type]

        if limit:
            messages = messages[-limit:]

        return messages

    def get_conversation_history(
        self,
        limit: Optional[int] = None,
        format: str = "openai"
    ) -> List[Dict[str, str]]:
        """
        获取对话历史（格式化为LLM输入格式）

        Args:
            limit: 限制数量
            format: 格式类型（openai/anthropic等）

        Returns:
            格式化的对话历史
        """
        messages = self.get_message_history(limit=limit)

        if format == "openai":
            return self._format_openai_messages(messages)
        else:
            return self._format_openai_messages(messages)

    def _format_openai_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """
        格式化为OpenAI消息格式

        Args:
            messages: 消息列表

        Returns:
            OpenAI格式的消息列表
        """
        formatted = []

        for msg in messages:
            # 根据消息类型映射角色
            if msg.sender == "user":
                role = "user"
            elif msg.sender == "system":
                role = "system"
            else:
                role = "assistant"

            formatted.append({
                "role": role,
                "content": msg.content
            })

        return formatted

    def clear_history(self):
        """清空消息历史"""
        self.message_history.clear()

    def get_context_data(self, key: str, default: Any = None) -> Any:
        """
        从当前上下文获取数据

        Args:
            key: 键名
            default: 默认值

        Returns:
            数据值
        """
        context = self.get_context()
        if context:
            return context.get(key, default)
        return default

    def set_context_data(self, key: str, value: Any):
        """
        设置当前上下文数据

        Args:
            key: 键名
            value: 值
        """
        context = self.get_context()
        if context:
            context.set(key, value)
        else:
            # 如果没有当前上下文，创建一个默认的
            import uuid
            context_id = str(uuid.uuid4())
            context = self.create_context(context_id)
            context.set(key, value)

    def get_summary(self) -> Dict[str, Any]:
        """
        获取上下文摘要

        Returns:
            摘要信息
        """
        return {
            "total_contexts": len(self.contexts),
            "current_context_id": self.current_context_id,
            "message_count": len(self.message_history),
            "max_history": self.max_history
        }

    def reset(self):
        """重置上下文管理器"""
        self.contexts.clear()
        self.message_history.clear()
        self.current_context_id = None
