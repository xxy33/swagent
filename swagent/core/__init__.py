"""
SWAgent 核心模块

包含Agent基类、消息系统、上下文管理、通信协议等核心组件
"""

from swagent.core.base_agent import BaseAgent, AgentConfig, AgentState
from swagent.core.message import (
    Message, 
    MessageType, 
    MessageContent,
    ContentType,
    ThinkResult,
    ActionResult
)
from swagent.core.context import (
    ContextManager,
    ContextScope,
    ExecutionContext
)
from swagent.core.communication import (
    MessageBus,
    AgentCommunicator,
    CommunicationPattern
)
from swagent.core.orchestrator import (
    Orchestrator,
    TaskDefinition,
    TaskResult,
    OrchestrationMode
)

__all__ = [
    # Agent基类
    "BaseAgent",
    "AgentConfig",
    "AgentState",
    
    # 消息系统
    "Message",
    "MessageType",
    "MessageContent",
    "ContentType",
    "ThinkResult",
    "ActionResult",
    
    # 上下文管理
    "ContextManager",
    "ContextScope",
    "ExecutionContext",
    
    # 通信系统
    "MessageBus",
    "AgentCommunicator",
    "CommunicationPattern",
    
    # 编排系统
    "Orchestrator",
    "TaskDefinition",
    "TaskResult",
    "OrchestrationMode",
]
