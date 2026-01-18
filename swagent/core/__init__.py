"""
SWAgent 核心模块

包含Agent基类、消息系统、上下文管理、通信协议等核心组件
"""

# 阶段1+2+3：已实现的模块
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
from swagent.core.base_agent import (
    BaseAgent,
    AgentConfig,
    AgentState
)
from swagent.core.communication import (
    MessageBus,
    AgentCommunicator,
    CommunicationPattern,
    RateLimitConfig,
    RateLimiter,
    TurnManager
)
from swagent.core.orchestrator import (
    Orchestrator,
    TaskDefinition,
    TaskResult,
    OrchestrationMode
)

__all__ = [
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

    # Agent基类
    "BaseAgent",
    "AgentConfig",
    "AgentState",

    # 通信系统
    "MessageBus",
    "AgentCommunicator",
    "CommunicationPattern",
    "RateLimitConfig",
    "RateLimiter",
    "TurnManager",

    # 编排系统
    "Orchestrator",
    "TaskDefinition",
    "TaskResult",
    "OrchestrationMode",
]
