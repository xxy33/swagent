"""
编排调度器
负责多Agent协作的编排和调度
"""
import asyncio
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from swagent.core.base_agent import BaseAgent
from swagent.core.message import Message, MessageType
from swagent.core.communication import MessageBus, AgentCommunicator, RateLimitConfig
from swagent.utils.logger import get_logger


logger = get_logger(__name__)


class OrchestrationMode(Enum):
    """编排模式"""
    SEQUENTIAL = "sequential"        # 顺序执行
    PARALLEL = "parallel"           # 并行执行
    DEBATE = "debate"              # 辩论模式（轮流发言）
    COLLABORATIVE = "collaborative" # 协作模式（自由发言）


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class TaskDefinition:
    """任务定义"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    input_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    """任务结果"""
    task_id: str
    status: TaskStatus
    output: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    agent_results: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> Optional[float]:
        """任务执行时长（秒）"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class Orchestrator:
    """
    编排调度器
    协调多个Agent完成复杂任务
    """

    def __init__(
        self,
        mode: OrchestrationMode = OrchestrationMode.COLLABORATIVE,
        enable_rate_limit: bool = True,
        rate_limit_config: Optional[RateLimitConfig] = None
    ):
        """
        初始化编排器

        Args:
            mode: 编排模式
            enable_rate_limit: 是否启用限流
            rate_limit_config: 限流配置
        """
        self.mode = mode
        self.agents: Dict[str, BaseAgent] = {}
        self.primary_agent: Optional[BaseAgent] = None

        # 创建消息总线
        enable_turn = (mode == OrchestrationMode.DEBATE)
        self.message_bus = MessageBus(
            enable_rate_limit=enable_rate_limit,
            rate_limit_config=rate_limit_config,
            enable_turn_control=enable_turn
        )

        # 任务管理
        self.current_task: Optional[TaskDefinition] = None
        self.task_history: List[TaskResult] = []

        # 状态
        self.is_running = False

        logger.info(f"编排器初始化 - 模式: {mode.value}")

    def register_agent(self, agent: BaseAgent, is_primary: bool = False):
        """
        注册Agent

        Args:
            agent: Agent实例
            is_primary: 是否为主Agent
        """
        agent_id = agent.agent_id

        # 注册到内部字典
        self.agents[agent_id] = agent

        # 注册到消息总线
        self.message_bus.register_agent(agent_id, agent)

        # 为Agent设置通信器
        agent.communicator = AgentCommunicator(agent_id, self.message_bus)

        if is_primary:
            self.primary_agent = agent

        logger.info(f"Agent注册: {agent.config.name} ({'主' if is_primary else '副'})")

    def unregister_agent(self, agent_id: str):
        """注销Agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            self.message_bus.unregister_agent(agent_id)

    async def start(self):
        """启动编排器"""
        self.is_running = True
        logger.info("编排器已启动")

    async def stop(self):
        """停止编排器"""
        self.is_running = False
        logger.info("编排器已停止")

    async def execute(
        self,
        task: TaskDefinition,
        timeout: Optional[float] = None
    ) -> TaskResult:
        """
        执行任务

        Args:
            task: 任务定义
            timeout: 超时时间（秒）

        Returns:
            任务结果
        """
        if not self.is_running:
            await self.start()

        self.current_task = task
        result = TaskResult(
            task_id=task.task_id,
            status=TaskStatus.RUNNING,
            started_at=datetime.now()
        )

        logger.info(f"开始执行任务: {task.name} ({task.task_id})")

        try:
            # 根据模式执行
            if self.mode == OrchestrationMode.SEQUENTIAL:
                output = await self._execute_sequential(task, timeout)
            elif self.mode == OrchestrationMode.PARALLEL:
                output = await self._execute_parallel(task, timeout)
            elif self.mode == OrchestrationMode.DEBATE:
                output = await self._execute_debate(task, timeout)
            else:  # COLLABORATIVE
                output = await self._execute_collaborative(task, timeout)

            result.status = TaskStatus.COMPLETED
            result.output = output

        except asyncio.TimeoutError:
            result.status = TaskStatus.TIMEOUT
            result.error = "任务执行超时"
            logger.error(f"任务超时: {task.task_id}")

        except Exception as e:
            result.status = TaskStatus.FAILED
            result.error = str(e)
            logger.error(f"任务执行失败: {str(e)}", exc_info=True)

        finally:
            result.completed_at = datetime.now()
            self.task_history.append(result)

        logger.info(f"任务完成: {task.name} - 状态: {result.status.value}, 耗时: {result.duration:.2f}秒")

        return result

    async def _execute_sequential(
        self,
        task: TaskDefinition,
        timeout: Optional[float]
    ) -> Any:
        """顺序执行"""
        results = []

        for agent in self.agents.values():
            message = Message(
                sender="orchestrator",
                receiver=agent.agent_id,
                content=task.description,
                msg_type=MessageType.TASK
            )

            response = await agent.run(message)
            results.append({
                "agent": agent.config.name,
                "response": response.content
            })

        return results

    async def _execute_parallel(
        self,
        task: TaskDefinition,
        timeout: Optional[float]
    ) -> Any:
        """并行执行"""
        tasks = []

        for agent in self.agents.values():
            message = Message(
                sender="orchestrator",
                receiver=agent.agent_id,
                content=task.description,
                msg_type=MessageType.TASK
            )

            tasks.append(agent.run(message))

        responses = await asyncio.gather(*tasks)

        results = []
        for agent, response in zip(self.agents.values(), responses):
            results.append({
                "agent": agent.config.name,
                "response": response.content
            })

        return results

    async def _execute_debate(
        self,
        task: TaskDefinition,
        timeout: Optional[float],
        max_rounds: int = 5
    ) -> Any:
        """
        辩论模式执行

        Args:
            task: 任务定义
            timeout: 超时时间
            max_rounds: 最大辩论轮数

        Returns:
            辩论结果
        """
        # 设置轮流发言顺序
        agent_ids = list(self.agents.keys())
        self.message_bus.setup_turn_control(agent_ids, round_robin=True)

        logger.info(f"开始辩论 - 参与者: {len(agent_ids)}, 最大轮数: {max_rounds}")

        # 辩论主题
        topic = task.description

        for round_num in range(1, max_rounds + 1):
            logger.info(f"--- 辩论第 {round_num} 轮 ---")

            for agent_id in agent_ids:
                agent = self.agents[agent_id]

                # 构建提示（包含历史）
                debate_history = self.message_bus.get_debate_history()
                if debate_history:
                    history_text = "\n".join([
                        f"[{msg['agent']}]: {msg['content']}"
                        for msg in debate_history
                    ])
                    prompt = f"辩论主题: {topic}\n\n之前的发言:\n{history_text}\n\n现在轮到你发言，请表达你的观点："
                else:
                    prompt = f"辩论主题: {topic}\n\n请表达你的观点："

                # Agent发言
                response_content = await agent.chat(prompt, use_history=False)

                # 广播发言
                await agent.communicator.broadcast(
                    content=response_content,
                    msg_type=MessageType.RESPONSE
                )

                logger.info(f"[{agent.config.name}]: {response_content[:100]}...")

                # 切换到下一个发言者
                self.message_bus.next_turn()

                # 小延迟，避免过快
                await asyncio.sleep(0.1)

        # 获取完整辩论历史
        debate_result = {
            "topic": topic,
            "rounds": max_rounds,
            "history": self.message_bus.get_debate_history(),
            "total_messages": len(self.message_bus.message_history)
        }

        return debate_result

    async def _execute_collaborative(
        self,
        task: TaskDefinition,
        timeout: Optional[float]
    ) -> Any:
        """协作模式执行（自由发言，但有限流）"""
        # 简化实现：每个Agent轮流发言一次
        results = []

        for agent in self.agents.values():
            message = Message(
                sender="orchestrator",
                content=task.description,
                msg_type=MessageType.TASK
            )

            response = await agent.run(message)
            results.append({
                "agent": agent.config.name,
                "response": response.content
            })

        return results

    async def debate_with_judgment(
        self,
        topic: str,
        max_rounds: int = 10,
        judge_agent: Optional['BaseAgent'] = None
    ) -> Dict[str, Any]:
        """
        带判断的辩论

        Args:
            topic: 辩论主题
            max_rounds: 最大轮数
            judge_agent: 判断Agent（ReActAgent）

        Returns:
            辩论结果
        """
        from swagent.agents.react_agent import ReActAgent

        # 如果没有提供判断Agent，创建一个
        if judge_agent is None:
            judge_agent = ReActAgent.create(name="辩论裁判")

        # 设置轮流发言
        agent_ids = list(self.agents.keys())
        self.message_bus.setup_turn_control(agent_ids, round_robin=True)

        logger.info(f"开始辩论（带判断） - 主题: {topic}")

        should_stop = False
        current_round = 0

        while current_round < max_rounds and not should_stop:
            current_round += 1
            logger.info(f"=== 第 {current_round} 轮 ===")

            # 每个Agent发言
            for agent_id in agent_ids:
                agent = self.agents[agent_id]

                # 构建提示
                debate_history = self.message_bus.get_debate_history()
                if debate_history:
                    history_text = "\n".join([
                        f"[{msg['agent']}]: {msg['content']}"
                        for msg in debate_history[-6:]  # 只显示最近6条
                    ])
                    prompt = f"辩论主题: {topic}\n\n最近的发言:\n{history_text}\n\n现在轮到你发言："
                else:
                    prompt = f"辩论主题: {topic}\n\n请首先表达你的观点："

                # Agent发言
                response_content = await agent.chat(prompt, use_history=False)

                # 广播发言
                await agent.communicator.broadcast(
                    content=response_content,
                    msg_type=MessageType.RESPONSE
                )

                logger.info(f"[{agent.config.name}]: {response_content[:80]}...")

                # 切换发言者
                self.message_bus.next_turn()

            # 每轮结束后判断
            debate_history = self.message_bus.get_debate_history()
            should_stop, judgment = await judge_agent.should_terminate_debate(
                debate_history=debate_history,
                current_round=current_round,
                max_rounds=max_rounds,
                min_confidence=0.7
            )

            if should_stop:
                logger.info(f"判断终止辩论 - 理由: {judgment.reason}")
                logger.info(f"决策: {judgment.decision.value}, 置信度: {judgment.confidence}")

        # 返回结果
        final_history = self.message_bus.get_debate_history()

        return {
            "topic": topic,
            "total_rounds": current_round,
            "terminated_by_judgment": should_stop,
            "judgment": judgment if should_stop else None,
            "history": final_history,
            "total_messages": len(final_history)
        }

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "mode": self.mode.value,
            "total_agents": len(self.agents),
            "is_running": self.is_running,
            "total_tasks": len(self.task_history),
            "message_bus_stats": self.message_bus.get_stats()
        }
