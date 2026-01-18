# 多Agent通信设计方案

## 📋 设计目标

1. **高效路由** - 快速准确地将消息传递给目标Agent
2. **灵活模式** - 支持多种通信模式（点对点、广播、订阅等）
3. **可追踪** - 完整的消息历史和状态跟踪
4. **可扩展** - 易于添加新的通信模式和功能
5. **容错性** - 消息重试、超时处理、错误恢复

## 🏗️ 架构设计

### 1. 核心组件

#### MessageBus（消息总线）
中央消息调度中心，负责：
- 消息路由和分发
- 消息队列管理
- 通信模式实现
- 消息持久化（可选）

```python
class MessageBus:
    """消息总线 - 中央调度"""

    def __init__(self):
        self.agents = {}                    # Agent注册表
        self.message_queues = {}            # 每个Agent的消息队列
        self.message_history = []           # 全局消息历史
        self.subscriptions = {}             # 主题订阅

    async def send(self, message: Message):
        """发送消息"""
        pass

    async def broadcast(self, message: Message):
        """广播消息"""
        pass

    def subscribe(self, agent_id: str, topic: str):
        """订阅主题"""
        pass
```

#### AgentCommunicator（Agent通信器）
每个Agent的通信接口，负责：
- 发送消息到总线
- 接收来自总线的消息
- 维护通信状态

```python
class AgentCommunicator:
    """Agent通信器"""

    def __init__(self, agent_id: str, message_bus: MessageBus):
        self.agent_id = agent_id
        self.bus = message_bus
        self.inbox = asyncio.Queue()       # 收件箱

    async def send_to(self, target: str, content: str):
        """发送给特定Agent"""
        pass

    async def broadcast(self, content: str):
        """广播给所有Agent"""
        pass

    async def receive(self) -> Message:
        """接收消息"""
        return await self.inbox.get()
```

### 2. 信息管理策略

#### A. 消息存储

**方案1：内存队列（默认）**
```python
# 优点：快速、简单
# 缺点：不持久化
agent_queues: Dict[str, asyncio.Queue[Message]]
```

**方案2：Redis队列（可选）**
```python
# 优点：持久化、分布式
# 缺点：需要外部依赖
# 用于生产环境或需要持久化的场景
```

**方案3：数据库（可选）**
```python
# 优点：完整历史、可查询
# 缺点：性能开销
# 用于需要审计和分析的场景
```

#### B. 消息路由表

```python
class RoutingTable:
    """消息路由表"""

    # 直接路由：Agent ID -> 队列
    direct_routes: Dict[str, Queue]

    # 主题路由：Topic -> Set[Agent IDs]
    topic_routes: Dict[str, Set[str]]

    # 模式路由：Pattern -> Handler
    pattern_routes: Dict[str, Callable]
```

#### C. 消息状态跟踪

```python
class MessageStatus(Enum):
    PENDING = "pending"       # 待发送
    SENT = "sent"            # 已发送
    DELIVERED = "delivered"   # 已送达
    PROCESSED = "processed"   # 已处理
    FAILED = "failed"        # 失败

class MessageTracker:
    """消息状态跟踪"""

    message_states: Dict[str, MessageStatus]
    delivery_confirmations: Dict[str, datetime]
    retry_counts: Dict[str, int]
```

### 3. 通信模式实现

#### 模式1：点对点（Point-to-Point）

```python
async def send_p2p(sender: str, receiver: str, message: Message):
    """
    A -> B 直接通信

    流程：
    1. 验证receiver存在
    2. 将消息加入receiver的队列
    3. 记录发送历史
    4. 返回发送确认
    """
    if receiver not in self.agents:
        raise AgentNotFoundError(receiver)

    await self.message_queues[receiver].put(message)
    self.message_history.append(message)
```

#### 模式2：广播（Broadcast）

```python
async def broadcast(sender: str, message: Message):
    """
    A -> 所有Agent

    流程：
    1. 获取所有在线Agent
    2. 并发发送给所有Agent
    3. 收集发送结果
    """
    tasks = []
    for agent_id in self.agents.keys():
        if agent_id != sender:  # 排除发送者自己
            task = self.message_queues[agent_id].put(message)
            tasks.append(task)

    await asyncio.gather(*tasks)
```

#### 模式3：发布订阅（Publish-Subscribe）

```python
async def publish(topic: str, message: Message):
    """
    发布到主题

    流程：
    1. 查找订阅该主题的Agent
    2. 发送给所有订阅者
    """
    if topic not in self.subscriptions:
        return

    subscribers = self.subscriptions[topic]
    for agent_id in subscribers:
        await self.message_queues[agent_id].put(message)

def subscribe(agent_id: str, topic: str):
    """订阅主题"""
    if topic not in self.subscriptions:
        self.subscriptions[topic] = set()
    self.subscriptions[topic].add(agent_id)
```

#### 模式4：请求-响应（Request-Reply）

```python
async def request_reply(sender: str, receiver: str, request: Message, timeout: int = 30):
    """
    请求-响应模式

    流程：
    1. 发送请求
    2. 等待响应（带超时）
    3. 返回响应
    """
    # 发送请求
    await self.send_p2p(sender, receiver, request)

    # 等待响应
    response = await asyncio.wait_for(
        self._wait_for_response(request.id),
        timeout=timeout
    )

    return response
```

### 4. 消息优先级管理

```python
class MessagePriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3

# 使用优先级队列
class PriorityMessageQueue:
    def __init__(self):
        self.queue = PriorityQueue()

    async def put(self, message: Message):
        # 根据优先级插入
        priority = message.priority
        await self.queue.put((priority, message))
```

### 5. 消息过滤和中间件

```python
class MessageFilter:
    """消息过滤器"""

    async def filter(self, message: Message) -> bool:
        """决定是否传递消息"""
        pass

class MessageMiddleware:
    """消息中间件"""

    async def process(self, message: Message) -> Message:
        """处理消息（如：加密、压缩、日志）"""
        pass

# 在MessageBus中使用
async def send(self, message: Message):
    # 应用中间件
    for middleware in self.middlewares:
        message = await middleware.process(message)

    # 应用过滤器
    for filter in self.filters:
        if not await filter.filter(message):
            return

    # 路由消息
    await self._route_message(message)
```

### 6. 错误处理和重试

```python
class RetryStrategy:
    """重试策略"""

    max_retries: int = 3
    retry_delay: float = 1.0
    backoff_factor: float = 2.0

async def send_with_retry(message: Message):
    """带重试的发送"""
    for attempt in range(self.retry_strategy.max_retries):
        try:
            await self.send(message)
            return True
        except Exception as e:
            if attempt < self.retry_strategy.max_retries - 1:
                delay = self.retry_strategy.retry_delay * (
                    self.retry_strategy.backoff_factor ** attempt
                )
                await asyncio.sleep(delay)
            else:
                # 记录失败
                self.failed_messages.append((message, e))
                return False
```

## 📊 数据流示例

### 场景1：多Agent辩论

```
辩论开始
    │
    ├─► Agent1 发表观点
    │       │
    │       └─► MessageBus.broadcast()
    │               │
    │               ├─► Agent2 收到
    │               ├─► Agent3 收到
    │               └─► ReActJudge 收到
    │
    ├─► Agent2 回应
    │       │
    │       └─► MessageBus.broadcast()
    │               │
    │               └─► 所有Agent收到
    │
    └─► ReActJudge 判断
            │
            └─► 决定是否终止
```

### 场景2：任务协作

```
Orchestrator 分配任务
    │
    ├─► send_to(Agent1, task1)
    │       │
    │       └─► Agent1 处理
    │               │
    │               └─► publish("task1_done", result)
    │
    ├─► send_to(Agent2, task2)
    │       │
    │       └─► Agent2 处理
    │
    └─► subscribe("task*_done")
            │
            └─► 等待所有任务完成
```

## 🔍 监控和调试

### 消息追踪

```python
class MessageTracer:
    """消息追踪器"""

    def trace(self, message: Message):
        """记录消息路径"""
        logger.info(f"Message {message.id}:")
        logger.info(f"  From: {message.sender}")
        logger.info(f"  To: {message.receiver}")
        logger.info(f"  Type: {message.msg_type}")
        logger.info(f"  Time: {message.timestamp}")
```

### 性能监控

```python
class PerformanceMonitor:
    """性能监控"""

    # 统计指标
    messages_sent: int
    messages_received: int
    average_latency: float
    queue_sizes: Dict[str, int]

    def get_stats(self) -> Dict:
        return {
            "total_messages": self.messages_sent,
            "avg_latency_ms": self.average_latency * 1000,
            "queue_sizes": self.queue_sizes
        }
```

## 🎯 实现优先级

### 第一阶段（MVP）
1. ✅ MessageBus基础实现
2. ✅ 点对点通信
3. ✅ 广播通信
4. ✅ Agent注册和注销
5. ✅ 基本的消息历史

### 第二阶段（增强）
1. ⏳ 发布订阅模式
2. ⏳ 消息优先级
3. ⏳ 请求-响应模式
4. ⏳ 消息过滤器

### 第三阶段（高级）
1. ⏳ 消息持久化（Redis/DB）
2. ⏳ 分布式支持
3. ⏳ 高级重试策略
4. ⏳ 性能监控

## 💡 设计权衡

### 选择中心化消息总线的原因：

**优点：**
- 简单易懂
- 集中管理和监控
- 易于实现消息历史和追踪
- 适合中小规模系统

**缺点：**
- 单点故障风险（可通过主备解决）
- 扩展性受限（可通过分片解决）

### 替代方案：

1. **去中心化P2P** - Agent直接通信，无中央总线
2. **混合模式** - 本地消息用P2P，跨组用总线

## 📝 使用示例

```python
# 创建消息总线
bus = MessageBus()

# 创建Agent
agent1 = PlannerAgent.create()
agent2 = PlannerAgent.create()
judge = ReActAgent.create()

# 注册到总线
bus.register_agent(agent1)
bus.register_agent(agent2)
bus.register_agent(judge)

# Agent1发送给Agent2
await agent1.communicator.send_to(
    target=agent2.agent_id,
    content="我们讨论一下垃圾分类方案"
)

# 广播消息
await agent1.communicator.broadcast(
    content="大家好，开始讨论"
)

# 订阅主题
judge.communicator.subscribe("debate_messages")

# 发布到主题
await bus.publish(
    topic="debate_messages",
    message=debate_update
)
```

---

**问题：你对这个设计有什么想法？**

我想知道：
1. 你更倾向于哪种存储方式？（内存 vs Redis vs DB）
2. 是否需要消息持久化？
3. 预期的Agent数量规模？（几个 vs 几十个 vs 更多）
4. 是否需要分布式支持？

根据你的需求，我可以调整实现方案的复杂度和功能重点。
