"""
StateGraph Workflow Engine
==========================

A LangGraph-inspired state graph workflow engine for building
multi-model collaboration workflows.

Example Usage:
-------------

```python
from swagent.stategraph import StateGraph, node, START, END
from typing import TypedDict

class MyState(TypedDict):
    input: str
    result: str

graph = StateGraph(MyState)

@graph.node()
async def process(state: MyState) -> dict:
    return {"result": state["input"].upper()}

graph.set_entry_point("process")
graph.set_exit_point("process")

app = graph.compile()
result = await app.invoke({"input": "hello"})
print(result.state["result"])  # "HELLO"
```

Key Components:
--------------
- StateGraph: Builder class for constructing graphs
- CompiledGraph: Executable graph with invoke/stream methods
- Node: Wraps functions with configuration and retry logic
- Edge: Connects nodes with fixed, conditional, or parallel routing
- StateManager: Handles state updates with merge strategies
- Persistence: Checkpoint storage for resumable workflows
- Error handling: Retry logic and custom error handlers
"""

# State management
from swagent.stategraph.state import (
    StateManager,
    StateSnapshot,
    MergeStrategy,
)

# Node definitions
from swagent.stategraph.node import (
    Node,
    NodeConfig,
    NodeResult,
    NodeStatus,
    node,
    START,
    END,
    is_special_node,
    get_node_name,
)

# Edge definitions
from swagent.stategraph.edge import (
    Edge,
    EdgeType,
    EdgeCollection,
    edge,
    conditional_edge,
    parallel_edge,
    loop_condition,
)

# Graph core
from swagent.stategraph.graph import (
    StateGraph,
    CompiledGraph,
    ExecutionConfig,
    ExecutionResult,
    GraphStatus,
    StreamEvent,
)

# Persistence
from swagent.stategraph.persistence import (
    WorkflowCheckpoint,
    BasePersistence,
    MemoryPersistence,
    LocalFilePersistence,
)

# Error handling
from swagent.stategraph.errors import (
    StateGraphError,
    NodeExecutionError,
    RetryExhaustedError,
    GraphValidationError,
    GraphExecutionError,
    TimeoutError,
    MaxIterationsError,
    RetryConfig,
    RetryHandler,
    BackoffStrategy,
    ErrorHandler,
    ErrorContext,
    with_retry,
    retry_config,
)

__all__ = [
    # State
    "StateManager",
    "StateSnapshot",
    "MergeStrategy",
    # Node
    "Node",
    "NodeConfig",
    "NodeResult",
    "NodeStatus",
    "node",
    "START",
    "END",
    "is_special_node",
    "get_node_name",
    # Edge
    "Edge",
    "EdgeType",
    "EdgeCollection",
    "edge",
    "conditional_edge",
    "parallel_edge",
    "loop_condition",
    # Graph
    "StateGraph",
    "CompiledGraph",
    "ExecutionConfig",
    "ExecutionResult",
    "GraphStatus",
    "StreamEvent",
    # Persistence
    "WorkflowCheckpoint",
    "BasePersistence",
    "MemoryPersistence",
    "LocalFilePersistence",
    # Errors
    "StateGraphError",
    "NodeExecutionError",
    "RetryExhaustedError",
    "GraphValidationError",
    "GraphExecutionError",
    "TimeoutError",
    "MaxIterationsError",
    "RetryConfig",
    "RetryHandler",
    "BackoffStrategy",
    "ErrorHandler",
    "ErrorContext",
    "with_retry",
    "retry_config",
]

__version__ = "0.1.0"
