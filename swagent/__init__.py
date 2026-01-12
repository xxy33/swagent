"""
SolidWaste-Agent (SWAgent)
面向固体废物领域的多智能体协作框架
"""

__version__ = "0.1.0"
__author__ = "SWAgent Team"
__license__ = "MIT"

from swagent.core.base_agent import BaseAgent, AgentConfig, AgentState
from swagent.core.message import Message, MessageType
from swagent.core.orchestrator import Orchestrator, TaskDefinition

__all__ = [
    "BaseAgent",
    "AgentConfig", 
    "AgentState",
    "Message",
    "MessageType",
    "Orchestrator",
    "TaskDefinition",
    "__version__",
]
