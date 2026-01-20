# StateGraph 工作流引擎

StateGraph 是一个类似 LangGraph 的状态图工作流引擎，用于构建复杂的多模型协作工作流。

## 目录

- [概述](#概述)
- [安装](#安装)
- [快速开始](#快速开始)
- [核心概念](#核心概念)
  - [State 状态管理](#state-状态管理)
  - [Node 节点定义](#node-节点定义)
  - [Edge 边定义](#edge-边定义)
  - [Graph 图定义](#graph-图定义)
- [高级功能](#高级功能)
  - [条件路由](#条件路由)
  - [并行执行](#并行执行)
  - [循环支持](#循环支持)
  - [状态持久化](#状态持久化)
  - [错误处理与重试](#错误处理与重试)
- [集成模块](#集成模块)
  - [LLM 节点](#llm-节点)
  - [Agent 节点](#agent-节点)
  - [Tool 节点](#tool-节点)
- [API 参考](#api-参考)

## 概述

StateGraph 工作流引擎提供了一种声明式的方式来定义和执行复杂的工作流。主要特性包括：

- **类型安全的状态管理**：使用 TypedDict 提供类型检查
- **灵活的节点定义**：支持同步/异步函数，装饰器模式
- **多种边类型**：固定边、条件边、并行边
- **循环支持**：支持循环模式，带最大迭代次数保护
- **状态持久化**：支持检查点保存和恢复
- **完善的错误处理**：可配置的重试策略和错误处理器

## 安装

StateGraph 是 swagent 的一部分，无需额外安装：

```python
from swagent.stategraph import StateGraph, node, START, END
```

## 快速开始

### 基础示例

```python
import asyncio
from swagent.stategraph import StateGraph, node, START, END
from typing import TypedDict

# 1. 定义状态类型
class MyState(TypedDict):
    input: str
    result: str

# 2. 创建图
graph = StateGraph(MyState)

# 3. 定义节点
@graph.node()
async def process(state: MyState) -> dict:
    return {"result": state["input"].upper()}

# 4. 设置入口和出口
graph.set_entry_point("process")
graph.set_exit_point("process")

# 5. 编译并执行
app = graph.compile()

async def main():
    result = await app.invoke({"input": "hello"})
    print(result.state["result"])  # "HELLO"

asyncio.run(main())
```

### 多节点工作流

```python
from typing import TypedDict
from swagent.stategraph import StateGraph

class PipelineState(TypedDict):
    raw_data: str
    cleaned_data: str
    analysis: str

graph = StateGraph(PipelineState)

@graph.node()
async def fetch_data(state: PipelineState) -> dict:
    # 获取数据
    return {"raw_data": "some raw data"}

@graph.node()
async def clean_data(state: PipelineState) -> dict:
    # 清洗数据
    cleaned = state["raw_data"].strip().lower()
    return {"cleaned_data": cleaned}

@graph.node()
async def analyze(state: PipelineState) -> dict:
    # 分析数据
    return {"analysis": f"Analysis of: {state['cleaned_data']}"}

# 定义流程
graph.set_entry_point("fetch_data")
graph.add_edge("fetch_data", "clean_data")
graph.add_edge("clean_data", "analyze")
graph.set_exit_point("analyze")

app = graph.compile()
```

## 核心概念

### State 状态管理

状态是工作流中数据流动的载体。使用 TypedDict 定义状态结构：

```python
from typing import TypedDict, List, Optional
from swagent.stategraph import StateManager, MergeStrategy

class WorkflowState(TypedDict):
    messages: List[str]
    current_step: str
    result: Optional[str]
```

#### 状态合并策略

```python
from swagent.stategraph import MergeStrategy

# 覆盖模式（默认）- 新值覆盖旧值
MergeStrategy.OVERWRITE

# 追加模式 - 用于列表，追加到末尾
MergeStrategy.APPEND

# 合并模式 - 用于字典，深度合并
MergeStrategy.MERGE

# 保留模式 - 保留旧值，忽略新值
MergeStrategy.KEEP
```

#### StateManager 使用

```python
from swagent.stategraph import StateManager

# 创建状态管理器
manager = StateManager(initial_state={"count": 0})

# 更新状态
manager.update({"count": 1})

# 获取当前状态
current = manager.get_state()

# 获取状态快照
snapshot = manager.snapshot()

# 回滚到之前的状态
manager.rollback(steps=1)

# 获取历史记录
history = manager.get_history()
```

### Node 节点定义

节点是工作流中的执行单元。

#### 使用装饰器

```python
from swagent.stategraph import StateGraph

graph = StateGraph(MyState)

# 基础节点
@graph.node()
async def my_node(state: MyState) -> dict:
    return {"result": "done"}

# 带配置的节点
@graph.node(retry_count=3, timeout=30.0)
async def robust_node(state: MyState) -> dict:
    return {"result": "done"}
```

#### 使用 Node 类

```python
from swagent.stategraph import Node, NodeConfig

async def my_function(state: dict) -> dict:
    return {"result": state["input"] * 2}

config = NodeConfig(
    name="my_node",
    retry_count=3,
    timeout=30.0,
    metadata={"description": "My custom node"}
)

node = Node(my_function, config=config)
graph.add_node("my_node", node)
```

#### 特殊节点

```python
from swagent.stategraph import START, END

# START - 虚拟起始节点
graph.add_edge(START, "first_node")

# END - 虚拟结束节点
graph.add_edge("last_node", END)
```

### Edge 边定义

边定义了节点之间的连接关系。

#### 固定边

```python
# 方式1: 使用 add_edge
graph.add_edge("node_a", "node_b")

# 方式2: 使用 edge 函数
from swagent.stategraph import edge

e = edge("node_a", "node_b")
```

#### 条件边

```python
from swagent.stategraph import conditional_edge

# 定义路由函数
def route_decision(state: dict) -> str:
    if state.get("score", 0) > 80:
        return "high"
    elif state.get("score", 0) > 50:
        return "medium"
    else:
        return "low"

# 添加条件边
graph.add_conditional_edge(
    "evaluate",
    route_decision,
    {
        "high": "approve",
        "medium": "review",
        "low": "reject"
    }
)
```

#### 并行边

```python
from swagent.stategraph import parallel_edge

# 创建并行边 - 同时执行多个节点
graph.add_parallel_edge(
    "start",
    ["task_a", "task_b", "task_c"]
)
```

### Graph 图定义

#### StateGraph 构建

```python
from swagent.stategraph import StateGraph, ExecutionConfig

# 创建图
graph = StateGraph(MyState)

# 添加节点
graph.add_node("node_a", node_a)
graph.add_node("node_b", node_b)

# 添加边
graph.add_edge("node_a", "node_b")

# 设置入口和出口
graph.set_entry_point("node_a")
graph.set_exit_point("node_b")

# 验证图
validation = graph.validate()
if not validation["valid"]:
    print(validation["errors"])

# 编译
app = graph.compile()
```

#### 执行配置

```python
from swagent.stategraph import ExecutionConfig

config = ExecutionConfig(
    max_iterations=100,      # 最大迭代次数
    timeout=300.0,           # 总超时时间
    enable_persistence=True  # 启用持久化
)

app = graph.compile(config=config)
```

#### 执行方式

```python
# 同步执行
result = await app.invoke({"input": "data"})
print(result.state)
print(result.status)  # GraphStatus.COMPLETED

# 流式执行
async for event in app.stream({"input": "data"}):
    print(f"Node: {event.node_name}")
    print(f"State: {event.state}")
```

## 高级功能

### 条件路由

条件路由允许根据状态动态选择下一个节点：

```python
from typing import TypedDict
from swagent.stategraph import StateGraph, END

class ReviewState(TypedDict):
    document: str
    quality_score: float
    approved: bool

graph = StateGraph(ReviewState)

@graph.node()
async def analyze(state: ReviewState) -> dict:
    # 分析文档质量
    score = len(state["document"]) / 100  # 简化示例
    return {"quality_score": min(score, 1.0)}

@graph.node()
async def approve(state: ReviewState) -> dict:
    return {"approved": True}

@graph.node()
async def reject(state: ReviewState) -> dict:
    return {"approved": False}

@graph.node()
async def manual_review(state: ReviewState) -> dict:
    # 人工审核逻辑
    return {"approved": True}

# 路由函数
def quality_router(state: ReviewState) -> str:
    score = state.get("quality_score", 0)
    if score >= 0.8:
        return "auto_approve"
    elif score >= 0.5:
        return "manual"
    else:
        return "auto_reject"

graph.set_entry_point("analyze")
graph.add_conditional_edge(
    "analyze",
    quality_router,
    {
        "auto_approve": "approve",
        "manual": "manual_review",
        "auto_reject": "reject"
    }
)
graph.add_edge("approve", END)
graph.add_edge("reject", END)
graph.add_edge("manual_review", END)
```

### 并行执行

并行执行多个独立的任务：

```python
from typing import TypedDict, Optional
from swagent.stategraph import StateGraph, END

class ParallelState(TypedDict):
    input: str
    result_a: Optional[str]
    result_b: Optional[str]
    result_c: Optional[str]
    final_result: Optional[str]

graph = StateGraph(ParallelState)

@graph.node()
async def task_a(state: ParallelState) -> dict:
    return {"result_a": f"A processed: {state['input']}"}

@graph.node()
async def task_b(state: ParallelState) -> dict:
    return {"result_b": f"B processed: {state['input']}"}

@graph.node()
async def task_c(state: ParallelState) -> dict:
    return {"result_c": f"C processed: {state['input']}"}

@graph.node()
async def aggregate(state: ParallelState) -> dict:
    results = [
        state.get("result_a", ""),
        state.get("result_b", ""),
        state.get("result_c", "")
    ]
    return {"final_result": " | ".join(results)}

# 并行执行 task_a, task_b, task_c
graph.set_entry_point("task_a")  # 入口点
graph.add_parallel_edge("task_a", ["task_a", "task_b", "task_c"])

# 汇聚结果
graph.add_edge("task_a", "aggregate")
graph.add_edge("task_b", "aggregate")
graph.add_edge("task_c", "aggregate")
graph.set_exit_point("aggregate")
```

### 循环支持

支持循环模式，用于迭代处理：

```python
from typing import TypedDict
from swagent.stategraph import StateGraph, END, loop_condition

class LoopState(TypedDict):
    counter: int
    max_count: int
    results: list

graph = StateGraph(LoopState)

@graph.node()
async def process(state: LoopState) -> dict:
    new_results = state.get("results", []) + [f"item_{state['counter']}"]
    return {
        "counter": state["counter"] + 1,
        "results": new_results
    }

# 循环条件
def should_continue(state: LoopState) -> str:
    if state["counter"] < state["max_count"]:
        return "continue"
    return "done"

graph.set_entry_point("process")
graph.add_conditional_edge(
    "process",
    should_continue,
    {
        "continue": "process",  # 循环回自己
        "done": END
    }
)

# 使用 loop_condition 辅助函数
continue_condition = loop_condition(
    condition=lambda s: s["counter"] < s["max_count"],
    continue_to="process",
    exit_to=END
)
```

### 状态持久化

保存和恢复工作流状态：

```python
from swagent.stategraph import (
    StateGraph,
    LocalFilePersistence,
    MemoryPersistence,
    ExecutionConfig
)

# 文件持久化
persistence = LocalFilePersistence("./checkpoints")

# 内存持久化（测试用）
# persistence = MemoryPersistence()

config = ExecutionConfig(enable_persistence=True)
app = graph.compile(config=config, persistence=persistence)

# 执行并保存检查点
result = await app.invoke(initial_state, workflow_id="my-workflow-001")

# 恢复工作流
result = await app.resume(workflow_id="my-workflow-001")

# 列出所有检查点
checkpoints = await persistence.list_checkpoints()

# 加载特定检查点
checkpoint = await persistence.load("my-workflow-001")
```

### 错误处理与重试

#### 节点级重试

```python
from swagent.stategraph import Node, NodeConfig, RetryConfig, BackoffStrategy

# 配置重试
config = NodeConfig(
    name="api_call",
    retry_count=3,
    timeout=30.0
)

# 或使用 RetryConfig
retry_config = RetryConfig(
    max_retries=3,
    base_delay=1.0,
    max_delay=30.0,
    backoff=BackoffStrategy.EXPONENTIAL,
    retryable_exceptions=[TimeoutError, ConnectionError]
)
```

#### 使用装饰器

```python
from swagent.stategraph import with_retry, retry_config

@with_retry(max_retries=3, backoff=BackoffStrategy.EXPONENTIAL)
async def unreliable_operation():
    # 可能失败的操作
    pass

# 或使用 retry_config 装饰器
@retry_config(max_retries=5, base_delay=2.0)
async def another_operation():
    pass
```

#### 全局错误处理器

```python
from swagent.stategraph import ErrorHandler, ErrorContext

# 定义错误处理函数
async def handle_error(context: ErrorContext) -> dict:
    print(f"Error in {context.node_name}: {context.error}")
    # 返回恢复状态
    return {"error_message": str(context.error), "recovered": True}

# 创建错误处理器
handler = ErrorHandler()
handler.register(ValueError, handle_error)

# 使用默认处理器
handler.set_default(lambda ctx: {"error": str(ctx.error)})
```

## 集成模块

### LLM 节点

将 LLM 调用封装为节点：

```python
from swagent.stategraph.integrations import llm_node, LLMNodeConfig
from swagent.llm import OpenAIClient

llm = OpenAIClient.from_config_file()

# 创建 LLM 节点
chat_node = llm_node(
    llm,
    name="chat",
    system_prompt="You are a helpful assistant.",
    input_key="user_message",
    output_key="assistant_response",
    temperature=0.7
)

graph.add_node("chat", chat_node)
```

### Agent 节点

将 Agent 封装为节点：

```python
from swagent.stategraph.integrations import agent_node, AgentNodeConfig
from swagent.agents import ReactAgent

agent = ReactAgent(config=AgentConfig(name="analyst"))

# 创建 Agent 节点
analyst_node = agent_node(
    agent,
    name="analyze",
    input_key="data",
    output_key="analysis",
    message_format=True  # 使用 Message 对象
)

graph.add_node("analyze", analyst_node)
```

### Tool 节点

将 Tool 封装为节点：

```python
from swagent.stategraph.integrations import tool_node, ToolNodeConfig
from swagent.tools import WebSearchTool

search = WebSearchTool()

# 创建 Tool 节点
search_node = tool_node(
    search,
    name="search",
    param_mapping={"query": "search_query"},  # 状态键映射
    output_key="search_results"
)

graph.add_node("search", search_node)
```

## API 参考

### 状态管理

| 类/函数 | 描述 |
|--------|------|
| `StateManager` | 状态管理器，处理状态更新和历史 |
| `StateSnapshot` | 状态快照数据类 |
| `MergeStrategy` | 状态合并策略枚举 |

### 节点

| 类/函数 | 描述 |
|--------|------|
| `Node` | 节点类，封装执行函数 |
| `NodeConfig` | 节点配置数据类 |
| `NodeResult` | 节点执行结果 |
| `NodeStatus` | 节点状态枚举 |
| `@node` | 节点装饰器 |
| `START` | 虚拟起始节点 |
| `END` | 虚拟结束节点 |

### 边

| 类/函数 | 描述 |
|--------|------|
| `Edge` | 边类 |
| `EdgeType` | 边类型枚举 |
| `edge()` | 创建固定边 |
| `conditional_edge()` | 创建条件边 |
| `parallel_edge()` | 创建并行边 |
| `loop_condition()` | 创建循环条件 |

### 图

| 类/函数 | 描述 |
|--------|------|
| `StateGraph` | 图构建器 |
| `CompiledGraph` | 可执行图 |
| `ExecutionConfig` | 执行配置 |
| `ExecutionResult` | 执行结果 |
| `GraphStatus` | 图状态枚举 |
| `StreamEvent` | 流式事件 |

### 持久化

| 类/函数 | 描述 |
|--------|------|
| `WorkflowCheckpoint` | 检查点数据类 |
| `BasePersistence` | 持久化抽象基类 |
| `MemoryPersistence` | 内存持久化 |
| `LocalFilePersistence` | 文件持久化 |

### 错误处理

| 类/函数 | 描述 |
|--------|------|
| `StateGraphError` | 基础异常类 |
| `NodeExecutionError` | 节点执行异常 |
| `RetryExhaustedError` | 重试耗尽异常 |
| `GraphValidationError` | 图验证异常 |
| `RetryConfig` | 重试配置 |
| `RetryHandler` | 重试处理器 |
| `BackoffStrategy` | 退避策略枚举 |
| `ErrorHandler` | 错误处理器 |
| `@with_retry` | 重试装饰器 |

## 完整示例

### 多模型协作工作流

```python
import asyncio
from typing import TypedDict, Optional, List
from swagent.stategraph import StateGraph, END

class CollaborationState(TypedDict):
    topic: str
    research: Optional[str]
    analysis: Optional[str]
    summary: Optional[str]
    final_report: Optional[str]

graph = StateGraph(CollaborationState)

@graph.node()
async def research_model(state: CollaborationState) -> dict:
    """模型1: 研究收集"""
    topic = state["topic"]
    # 调用研究模型
    research = f"Research findings about {topic}..."
    return {"research": research}

@graph.node()
async def analysis_model(state: CollaborationState) -> dict:
    """模型2: 深度分析"""
    research = state.get("research", "")
    analysis = f"Analysis of: {research}"
    return {"analysis": analysis}

@graph.node()
async def summary_model(state: CollaborationState) -> dict:
    """模型3: 总结生成"""
    analysis = state.get("analysis", "")
    summary = f"Summary: {analysis[:100]}..."
    return {"summary": summary}

@graph.node()
async def report_generator(state: CollaborationState) -> dict:
    """最终报告生成"""
    report = f"""
    # Report: {state['topic']}

    ## Research
    {state.get('research', '')}

    ## Analysis
    {state.get('analysis', '')}

    ## Summary
    {state.get('summary', '')}
    """
    return {"final_report": report}

# 定义工作流
graph.set_entry_point("research_model")
graph.add_edge("research_model", "analysis_model")
graph.add_edge("analysis_model", "summary_model")
graph.add_edge("summary_model", "report_generator")
graph.set_exit_point("report_generator")

# 编译并执行
app = graph.compile()

async def main():
    result = await app.invoke({"topic": "Climate Change"})
    print(result.state["final_report"])

asyncio.run(main())
```

---

更多示例请参考 `examples/` 目录中的 StateGraph 相关示例。
