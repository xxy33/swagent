# ReAct Agent 文档

## 📖 概述

ReAct Agent 是一个基于 ReAct（Reasoning and Acting）模式的智能Agent，专门用于判断多Agent辩论何时应该终止。

## 🎯 核心功能

### 1. 辩论状态判断

ReAct Agent 可以判断辩论是否处于以下状态：

- **CONSENSUS（达成共识）**: 各方观点趋于一致，没有重大分歧
- **SUFFICIENT（信息充分）**: 关键信息已充分讨论，继续讨论收益递减
- **DIVERGENCE（分歧过大）**: 观点差异太大，需要外部介入或重新框架
- **CONTINUE（继续讨论）**: 还有价值的讨论空间，应继续
- **TIMEOUT（超时）**: 讨论轮次过多，应强制终止

### 2. ReAct 思考模式

每次判断都遵循 ReAct 模式：

1. **Thought（思考）**: 分析当前讨论状态
2. **Observation（观察）**: 总结关键信息和模式
3. **Action（决策）**: 做出决策并给出理由

### 3. 置信度评估

每个判断都附带置信度（0-1），表示Agent对决策的确定程度。

## 🚀 快速开始

### 基本使用

```python
import asyncio
from swagent import ReActAgent

async def main():
    # 创建ReAct Agent
    judge = ReActAgent.create(name="辩论裁判")

    # 辩论历史
    debate_history = [
        {"agent": "Agent1", "content": "我认为应该采用方案A"},
        {"agent": "Agent2", "content": "我同意，方案A确实更合理"},
        {"agent": "Agent1", "content": "那我们就这么定了"}
    ]

    # 判断辩论状态
    result = await judge.judge_debate_status(
        debate_history=debate_history,
        current_round=2,
        max_rounds=5
    )

    print(f"决策: {result.decision.value}")
    print(f"置信度: {result.confidence}")
    print(f"理由: {result.reason}")

asyncio.run(main())
```

### 判断是否应该终止

```python
# 简化的判断接口
should_stop, result = await judge.should_terminate_debate(
    debate_history=debate_history,
    current_round=3,
    max_rounds=10,
    min_confidence=0.7  # 最小置信度阈值
)

if should_stop:
    print(f"建议终止辩论，原因: {result.reason}")
else:
    print("建议继续讨论")
```

### 共识分析

```python
# 分析辩论的共识程度
result = await judge.analyze_consensus(debate_history)

print(result["analysis"])
```

## 📊 判断结果结构

`ThoughtResult` 对象包含以下信息：

```python
@dataclass
class ThoughtResult:
    reasoning: str          # 推理过程（Thought部分）
    observation: str        # 观察结果（Observation部分）
    decision: DebateStatus  # 决策结果
    confidence: float       # 置信度 (0-1)
    reason: str            # 决策理由
    suggestions: List[str] # 后续建议
```

## 🎨 使用场景

### 场景1: 多Agent辩论系统

在多Agent辩论系统中，使用ReAct Agent作为仲裁者：

```python
# 伪代码示例
debate_round = 0
max_rounds = 10

while debate_round < max_rounds:
    # 各个Agent发表观点
    for agent in debate_agents:
        response = await agent.debate(topic)
        debate_history.append({
            "agent": agent.name,
            "content": response
        })

    debate_round += 1

    # 判断是否应该终止
    should_stop, result = await judge.should_terminate_debate(
        debate_history=debate_history,
        current_round=debate_round,
        max_rounds=max_rounds
    )

    if should_stop:
        print(f"辩论终止: {result.reason}")
        break
```

### 场景2: 共识度评估

评估团队讨论的共识程度：

```python
# 分析讨论后的共识
consensus_result = await judge.analyze_consensus(debate_history)

# 根据共识度决定下一步
if "共识度评分：9" in consensus_result["analysis"]:
    print("共识度很高，可以进入决策阶段")
elif "共识度评分：[0-5]" in consensus_result["analysis"]:
    print("共识度较低，需要进一步讨论")
```

## ⚙️ 配置选项

### 创建时配置

```python
from swagent import AgentConfig, ReActAgent

config = AgentConfig(
    name="专业裁判",
    role="辩论仲裁者",
    model="gpt-4",
    temperature=0.3,      # 较低温度获得更稳定判断
    max_tokens=2048,
    max_iterations=5
)

judge = ReActAgent(config)
```

### 判断阈值配置

```python
should_stop, result = await judge.should_terminate_debate(
    debate_history=debate_history,
    current_round=round_num,
    max_rounds=10,          # 最大轮次
    min_confidence=0.7      # 最小置信度阈值
)
```

## 📝 最佳实践

### 1. 合理设置最大轮次

```python
# 根据讨论复杂度设置
simple_topic_max = 5      # 简单话题
complex_topic_max = 15    # 复杂话题
```

### 2. 调整置信度阈值

```python
# 重要决策使用高阈值
critical_decision_threshold = 0.8

# 一般讨论使用中等阈值
normal_threshold = 0.6
```

### 3. 处理判断结果

```python
should_stop, result = await judge.should_terminate_debate(...)

if should_stop:
    if result.decision == DebateStatus.CONSENSUS:
        # 达成共识，可以执行决策
        execute_decision(debate_history)
    elif result.decision == DebateStatus.DIVERGENCE:
        # 分歧过大，需要调解
        mediate_debate(debate_history)
    elif result.decision == DebateStatus.SUFFICIENT:
        # 信息充分，可以投票表决
        conduct_vote(debate_history)
```

### 4. 利用建议

```python
if result.suggestions:
    print("ReAct Agent的建议:")
    for suggestion in result.suggestions:
        print(f"  - {suggestion}")
        # 根据建议调整辩论流程
```

## 🔍 判断标准说明

### CONSENSUS（达成共识）

- 各方观点趋向一致
- 没有新的反对意见
- 核心结论已形成

### SUFFICIENT（信息充分）

- 关键问题已讨论
- 各方观点已充分表达
- 继续讨论边际收益低

### DIVERGENCE（分歧过大）

- 观点差异显著
- 讨论陷入僵局
- 需要外部介入

### CONTINUE（继续讨论）

- 仍有待讨论的观点
- 新信息持续出现
- 共识正在形成中

### TIMEOUT（超时）

- 达到最大轮次
- 讨论效率降低
- 强制终止以避免浪费

## 🧪 测试示例

运行测试：

```bash
# 完整测试
python tests/test_react_agent.py

# 使用示例
python examples/02_react_debate_judge.py
```

## 🎓 进阶用法

### 自定义判断逻辑

通过继承`ReActAgent`并重写`_parse_judgment_response`方法：

```python
class CustomReActAgent(ReActAgent):
    def _parse_judgment_response(self, response: str) -> ThoughtResult:
        # 自定义解析逻辑
        result = super()._parse_judgment_response(response)

        # 添加自定义规则
        if "紧急" in response:
            result.decision = DebateStatus.DIVERGENCE
            result.confidence = 1.0

        return result
```

### 集成到工作流

```python
from swagent import Orchestrator, ReActAgent, PlannerAgent

async def debate_workflow():
    # 创建编排器
    orchestrator = Orchestrator()

    # 创建辩论Agent和判断Agent
    debaters = [PlannerAgent.create(name=f"Agent{i}") for i in range(3)]
    judge = ReActAgent.create()

    # 运行辩论流程
    # ... (具体实现见阶段3)
```

## 📚 相关文档

- [Agent基础框架](PHASE2_SUMMARY.md)
- [多Agent通信](../core/communication.py) (待实现)
- [编排调度器](../core/orchestrator.py) (待实现)

---

**版本**: 0.1.0
**状态**: 已实现并测试通过
**测试覆盖**: 5/5 测试用例通过
