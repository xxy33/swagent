"""
SolidWaste-Agent (SWAgent)
面向固体废物领域的多智能体协作框架
"""

__version__ = "0.1.0"
__author__ = "SWAgent Team"
__license__ = "MIT"

# 阶段1+2+3：已实现的模块
from swagent.core.message import Message, MessageType
from swagent.core.context import ContextManager, ExecutionContext, ContextScope
from swagent.core.base_agent import BaseAgent, AgentConfig, AgentState
from swagent.core.communication import (
    MessageBus,
    AgentCommunicator,
    CommunicationPattern,
    RateLimitConfig,
    TurnManager
)
from swagent.core.orchestrator import (
    Orchestrator,
    TaskDefinition,
    TaskResult,
    OrchestrationMode
)
from swagent.agents.planner_agent import PlannerAgent
from swagent.agents.react_agent import ReActAgent, DebateStatus

__all__ = [
    # 消息系统
    "Message",
    "MessageType",

    # 上下文管理
    "ContextManager",
    "ExecutionContext",
    "ContextScope",

    # Agent基类
    "BaseAgent",
    "AgentConfig",
    "AgentState",

    # 通信系统
    "MessageBus",
    "AgentCommunicator",
    "CommunicationPattern",
    "RateLimitConfig",
    "TurnManager",

    # 编排系统
    "Orchestrator",
    "TaskDefinition",
    "TaskResult",
    "OrchestrationMode",

    # 具体Agent
    "PlannerAgent",
    "ReActAgent",
    "DebateStatus",

    "__version__",
]
