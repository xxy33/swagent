"""
通信系统
实现Agent间的消息传递、路由和管理
"""
import asyncio
from typing import Dict, Set, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid

from swagent.core.message import Message, MessageType
from swagent.utils.logger import get_logger


logger = get_logger(__name__)


class CommunicationPattern(Enum):
    """通信模式"""
    POINT_TO_POINT = "p2p"          # 点对点
    BROADCAST = "broadcast"          # 广播
    PUBLISH_SUBSCRIBE = "pubsub"     # 发布订阅
    REQUEST_REPLY = "req_reply"      # 请求-响应


class AgentStatus(Enum):
    """Agent状态"""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"


@dataclass
class RateLimitConfig:
    """限流配置"""
    max_messages_per_minute: int = 10  # 每分钟最大消息数
    max_messages_per_turn: int = 1      # 每轮最大消息数
    cooldown_seconds: float = 1.0       # 冷却时间（秒）


class RateLimiter:
    """
    消息限流器
    防止Agent刷屏
    """

    def __init__(self, config: RateLimitConfig):
        """
        初始化限流器

        Args:
            config: 限流配置
        """
        self.config = config
        # Agent ID -> 消息时间戳列表
        self.message_timestamps: Dict[str, List[datetime]] = {}
        # Agent ID -> 当前轮次消息计数
        self.turn_message_count: Dict[str, int] = {}
        # Agent ID -> 最后发送时间
        self.last_send_time: Dict[str, datetime] = {}

    def check_rate_limit(self, agent_id: str) -> tuple[bool, Optional[str]]:
        """
        检查是否超出限流

        Args:
            agent_id: Agent ID

        Returns:
            (是否允许, 拒绝理由)
        """
        now = datetime.now()

        # 检查冷却时间
        if agent_id in self.last_send_time:
            time_since_last = (now - self.last_send_time[agent_id]).total_seconds()
            if time_since_last < self.config.cooldown_seconds:
                return False, f"冷却中，请等待{self.config.cooldown_seconds - time_since_last:.1f}秒"

        # 检查每分钟限制
        if agent_id not in self.message_timestamps:
            self.message_timestamps[agent_id] = []

        # 清理1分钟前的记录
        one_minute_ago = now - timedelta(minutes=1)
        self.message_timestamps[agent_id] = [
            ts for ts in self.message_timestamps[agent_id]
            if ts > one_minute_ago
        ]

        if len(self.message_timestamps[agent_id]) >= self.config.max_messages_per_minute:
            return False, f"超出频率限制（{self.config.max_messages_per_minute}条/分钟）"

        # 检查当前轮次限制
        turn_count = self.turn_message_count.get(agent_id, 0)
        if turn_count >= self.config.max_messages_per_turn:
            return False, f"本轮发言次数已用完（{self.config.max_messages_per_turn}次/轮）"

        return True, None

    def record_message(self, agent_id: str):
        """
        记录消息发送

        Args:
            agent_id: Agent ID
        """
        now = datetime.now()

        # 记录时间戳
        if agent_id not in self.message_timestamps:
            self.message_timestamps[agent_id] = []
        self.message_timestamps[agent_id].append(now)

        # 记录最后发送时间
        self.last_send_time[agent_id] = now

        # 增加轮次计数
        self.turn_message_count[agent_id] = self.turn_message_count.get(agent_id, 0) + 1

    def reset_turn(self, agent_id: Optional[str] = None):
        """
        重置轮次计数

        Args:
            agent_id: Agent ID，None表示重置所有
        """
        if agent_id:
            self.turn_message_count[agent_id] = 0
        else:
            self.turn_message_count.clear()


class TurnManager:
    """
    轮流发言管理器
    控制Agent的发言顺序
    """

    def __init__(self, agent_ids: List[str], round_robin: bool = True):
        """
        初始化轮流管理器

        Args:
            agent_ids: Agent ID列表（按顺序）
            round_robin: 是否循环轮流
        """
        self.agent_ids = agent_ids
        self.round_robin = round_robin
        self.current_index = 0
        self.current_speaker: Optional[str] = None
        self.speaking_history: List[tuple[str, datetime]] = []

        # 设置第一个发言者
        if agent_ids:
            self.current_speaker = agent_ids[0]

    def get_current_speaker(self) -> Optional[str]:
        """获取当前可以发言的Agent"""
        return self.current_speaker

    def can_speak(self, agent_id: str) -> tuple[bool, Optional[str]]:
        """
        检查Agent是否可以发言

        Args:
            agent_id: Agent ID

        Returns:
            (是否可以发言, 拒绝理由)
        """
        if not self.current_speaker:
            return False, "没有设置当前发言者"

        if agent_id == self.current_speaker:
            return True, None
        else:
            return False, f"当前发言者是 {self.current_speaker}，请等待轮到你"

    def next_turn(self) -> Optional[str]:
        """
        切换到下一个发言者

        Returns:
            下一个发言者的Agent ID
        """
        if not self.agent_ids:
            return None

        # 记录发言历史
        if self.current_speaker:
            self.speaking_history.append((self.current_speaker, datetime.now()))

        # 切换到下一个
        if self.round_robin:
            self.current_index = (self.current_index + 1) % len(self.agent_ids)
        else:
            self.current_index = min(self.current_index + 1, len(self.agent_ids) - 1)

        self.current_speaker = self.agent_ids[self.current_index]
        logger.info(f"切换发言者: {self.current_speaker}")

        return self.current_speaker

    def reset(self):
        """重置到第一个发言者"""
        self.current_index = 0
        self.current_speaker = self.agent_ids[0] if self.agent_ids else None
        self.speaking_history.clear()

    def add_agent(self, agent_id: str):
        """添加Agent到轮流列表"""
        if agent_id not in self.agent_ids:
            self.agent_ids.append(agent_id)

    def remove_agent(self, agent_id: str):
        """从轮流列表移除Agent"""
        if agent_id in self.agent_ids:
            self.agent_ids.remove(agent_id)
            if self.current_speaker == agent_id:
                self.next_turn()


class MessageBus:
    """
    消息总线
    中央消息调度中心
    """

    def __init__(
        self,
        enable_rate_limit: bool = True,
        rate_limit_config: Optional[RateLimitConfig] = None,
        enable_turn_control: bool = False
    ):
        """
        初始化消息总线

        Args:
            enable_rate_limit: 是否启用限流
            rate_limit_config: 限流配置
            enable_turn_control: 是否启用轮流控制
        """
        # Agent注册表
        self.agents: Dict[str, 'BaseAgent'] = {}
        self.agent_status: Dict[str, AgentStatus] = {}

        # 消息队列（每个Agent一个队列）
        self.message_queues: Dict[str, asyncio.Queue] = {}

        # 消息历史
        self.message_history: List[Message] = []

        # 订阅关系（主题 -> Agent IDs）
        self.subscriptions: Dict[str, Set[str]] = {}

        # 限流器
        self.enable_rate_limit = enable_rate_limit
        if enable_rate_limit:
            config = rate_limit_config or RateLimitConfig()
            self.rate_limiter = RateLimiter(config)
        else:
            self.rate_limiter = None

        # 轮流管理器
        self.enable_turn_control = enable_turn_control
        self.turn_manager: Optional[TurnManager] = None

        logger.info(f"消息总线初始化 - 限流: {enable_rate_limit}, 轮流: {enable_turn_control}")

    def register_agent(self, agent_id: str, agent: 'BaseAgent'):
        """
        注册Agent

        Args:
            agent_id: Agent ID
            agent: Agent实例
        """
        self.agents[agent_id] = agent
        self.agent_status[agent_id] = AgentStatus.ONLINE
        self.message_queues[agent_id] = asyncio.Queue()

        logger.info(f"Agent注册成功: {agent_id}")

    def unregister_agent(self, agent_id: str):
        """
        注销Agent

        Args:
            agent_id: Agent ID
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
            del self.agent_status[agent_id]
            del self.message_queues[agent_id]
            logger.info(f"Agent注销: {agent_id}")

    def setup_turn_control(self, agent_ids: List[str], round_robin: bool = True):
        """
        设置轮流发言

        Args:
            agent_ids: Agent ID列表（按发言顺序）
            round_robin: 是否循环轮流
        """
        self.turn_manager = TurnManager(agent_ids, round_robin)
        self.enable_turn_control = True
        logger.info(f"启用轮流发言 - Agent数: {len(agent_ids)}, 循环: {round_robin}")

    async def send(
        self,
        message: Message,
        pattern: CommunicationPattern = CommunicationPattern.POINT_TO_POINT
    ) -> bool:
        """
        发送消息

        Args:
            message: 消息对象
            pattern: 通信模式

        Returns:
            是否发送成功
        """
        sender = message.sender

        # 检查轮流控制
        if self.enable_turn_control and self.turn_manager:
            can_speak, reason = self.turn_manager.can_speak(sender)
            if not can_speak:
                logger.warning(f"发言被拒绝 - {sender}: {reason}")
                return False

        # 检查限流
        if self.enable_rate_limit and self.rate_limiter:
            allowed, reason = self.rate_limiter.check_rate_limit(sender)
            if not allowed:
                logger.warning(f"消息被限流 - {sender}: {reason}")
                return False

        # 根据模式发送
        if pattern == CommunicationPattern.POINT_TO_POINT:
            success = await self._send_p2p(message)
        elif pattern == CommunicationPattern.BROADCAST:
            success = await self._send_broadcast(message)
        elif pattern == CommunicationPattern.PUBLISH_SUBSCRIBE:
            success = await self._send_pubsub(message)
        else:
            success = False

        if success:
            # 记录消息历史
            self.message_history.append(message)

            # 记录限流
            if self.enable_rate_limit and self.rate_limiter:
                self.rate_limiter.record_message(sender)

        return success

    async def _send_p2p(self, message: Message) -> bool:
        """点对点发送"""
        receiver = message.receiver

        if not receiver or receiver not in self.message_queues:
            logger.error(f"接收者不存在: {receiver}")
            return False

        await self.message_queues[receiver].put(message)
        logger.debug(f"P2P消息: {message.sender} -> {receiver}")
        return True

    async def _send_broadcast(self, message: Message) -> bool:
        """广播发送"""
        sender = message.sender
        tasks = []

        for agent_id, queue in self.message_queues.items():
            if agent_id != sender:  # 不发送给自己
                tasks.append(queue.put(message))

        if tasks:
            await asyncio.gather(*tasks)
            logger.debug(f"广播消息: {sender} -> {len(tasks)}个Agent")

        return True

    async def _send_pubsub(self, message: Message) -> bool:
        """发布订阅发送"""
        # 假设使用metadata中的topic
        topic = message.metadata.get('topic')
        if not topic or topic not in self.subscriptions:
            logger.warning(f"主题不存在: {topic}")
            return False

        subscribers = self.subscriptions[topic]
        tasks = []

        for agent_id in subscribers:
            if agent_id in self.message_queues:
                tasks.append(self.message_queues[agent_id].put(message))

        if tasks:
            await asyncio.gather(*tasks)
            logger.debug(f"发布到主题 {topic}: {len(tasks)}个订阅者")

        return True

    def subscribe(self, agent_id: str, topic: str):
        """
        订阅主题

        Args:
            agent_id: Agent ID
            topic: 主题名称
        """
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()

        self.subscriptions[topic].add(agent_id)
        logger.info(f"{agent_id} 订阅主题: {topic}")

    def unsubscribe(self, agent_id: str, topic: str):
        """取消订阅"""
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(agent_id)

    async def receive(self, agent_id: str, timeout: Optional[float] = None) -> Optional[Message]:
        """
        接收消息

        Args:
            agent_id: Agent ID
            timeout: 超时时间（秒）

        Returns:
            消息对象，超时返回None
        """
        if agent_id not in self.message_queues:
            return None

        try:
            if timeout:
                message = await asyncio.wait_for(
                    self.message_queues[agent_id].get(),
                    timeout=timeout
                )
            else:
                message = await self.message_queues[agent_id].get()

            return message
        except asyncio.TimeoutError:
            return None

    def get_message_history(
        self,
        limit: Optional[int] = None,
        agent_id: Optional[str] = None
    ) -> List[Message]:
        """
        获取消息历史

        Args:
            limit: 限制数量
            agent_id: 过滤特定Agent的消息

        Returns:
            消息列表
        """
        messages = self.message_history

        if agent_id:
            messages = [m for m in messages if m.sender == agent_id or m.receiver == agent_id]

        if limit:
            messages = messages[-limit:]

        return messages

    def get_debate_history(self) -> List[Dict[str, str]]:
        """
        获取辩论历史（格式化为ReAct Agent可用的格式）

        Returns:
            辩论历史列表
        """
        history = []
        for msg in self.message_history:
            if msg.msg_type in [MessageType.REQUEST, MessageType.RESPONSE]:
                agent_name = self.agents[msg.sender].config.name if msg.sender in self.agents else msg.sender
                history.append({
                    "agent": agent_name,
                    "content": msg.content
                })
        return history

    def next_turn(self) -> Optional[str]:
        """切换到下一个发言者"""
        if self.turn_manager:
            next_speaker = self.turn_manager.next_turn()

            # 重置限流器的轮次计数
            if self.rate_limiter:
                self.rate_limiter.reset_turn()

            return next_speaker
        return None

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "total_agents": len(self.agents),
            "online_agents": len([s for s in self.agent_status.values() if s == AgentStatus.ONLINE]),
            "total_messages": len(self.message_history),
            "queue_sizes": {
                agent_id: queue.qsize()
                for agent_id, queue in self.message_queues.items()
            },
            "current_speaker": self.turn_manager.get_current_speaker() if self.turn_manager else None
        }


class AgentCommunicator:
    """
    Agent通信器
    每个Agent的通信接口
    """

    def __init__(self, agent_id: str, message_bus: MessageBus):
        """
        初始化通信器

        Args:
            agent_id: Agent ID
            message_bus: 消息总线
        """
        self.agent_id = agent_id
        self.bus = message_bus

    async def send_to(self, target: str, content: str, msg_type: MessageType = MessageType.REQUEST) -> bool:
        """
        发送给特定Agent

        Args:
            target: 目标Agent ID
            content: 消息内容
            msg_type: 消息类型

        Returns:
            是否发送成功
        """
        message = Message(
            sender=self.agent_id,
            receiver=target,
            content=content,
            msg_type=msg_type
        )

        return await self.bus.send(message, CommunicationPattern.POINT_TO_POINT)

    async def broadcast(self, content: str, msg_type: MessageType = MessageType.REQUEST) -> bool:
        """
        广播消息

        Args:
            content: 消息内容
            msg_type: 消息类型

        Returns:
            是否发送成功
        """
        message = Message(
            sender=self.agent_id,
            content=content,
            msg_type=msg_type
        )

        return await self.bus.send(message, CommunicationPattern.BROADCAST)

    async def publish(self, topic: str, content: str) -> bool:
        """
        发布到主题

        Args:
            topic: 主题名称
            content: 消息内容

        Returns:
            是否发送成功
        """
        message = Message(
            sender=self.agent_id,
            content=content,
            msg_type=MessageType.INFORM,
            metadata={"topic": topic}
        )

        return await self.bus.send(message, CommunicationPattern.PUBLISH_SUBSCRIBE)

    def subscribe(self, topic: str):
        """订阅主题"""
        self.bus.subscribe(self.agent_id, topic)

    async def receive(self, timeout: Optional[float] = None) -> Optional[Message]:
        """
        接收消息

        Args:
            timeout: 超时时间

        Returns:
            消息对象
        """
        return await self.bus.receive(self.agent_id, timeout)
