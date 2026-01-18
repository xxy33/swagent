# SWAgent 架构设计文档

本文档详细描述 SWAgent 系统的整体架构、设计理念和技术实现。

## 目录

- [设计理念](#设计理念)
- [系统架构](#系统架构)
- [模块设计](#模块设计)
- [数据流](#数据流)
- [扩展性设计](#扩展性设计)
- [性能考虑](#性能考虑)

---

## 设计理念

### 核心原则

1. **模块化设计**: 各功能模块独立，低耦合高内聚
2. **协议无关**: 支持多种 LLM 协议和工具调用格式
3. **领域驱动**: 针对固废管理领域深度优化
4. **异步优先**: 全面采用异步编程提升性能
5. **可扩展性**: 易于添加新功能和集成新模型

### 架构目标

- **灵活性**: 支持不同 LLM 提供商和本地部署
- **可靠性**: 完善的错误处理和重试机制
- **可维护性**: 清晰的代码结构和完整文档
- **性能**: 高效的异步执行和资源管理
- **专业性**: 领域知识深度集成

---

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         应用层 (Application)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   示例程序   │  │   测试套件   │  │   CLI 工具   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      工作流层 (Workflow)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ 科研工作流   │  │ 报告工作流   │  │ 分析工作流   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌────────────────────────────────┐          │
│  │ 编码工作流   │  │      工作流管理器              │          │
│  └──────────────┘  └────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────────┐
│                    领域增强层 (Domain)                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   知识库     │  │   术语库     │  │   标准库     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌────────────────────────────────┐          │
│  │ 领域提示词   │  │      领域数据 (JSON)           │          │
│  └──────────────┘  └────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      工具层 (Tools)                              │
│  ┌──────────────────────────────────────────────────┐          │
│  │              工具注册中心 (Tool Registry)         │          │
│  └──────────────────────────────────────────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  内置工具    │  │  领域工具    │  │  自定义工具  │          │
│  │  - 代码执行  │  │  - 排放计算  │  │             │          │
│  │  - 文件处理  │  │  - LCA 分析  │  │             │          │
│  │  - 网络搜索  │  │  - 可视化    │  │             │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌────────────────────────────────────────────────┐            │
│  │  协议适配: OpenAI Function / MCP                │            │
│  └────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      Agent 层 (Agent)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ PlannerAgent │  │  ReActAgent  │  │  CustomAgent │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────────────────────────────────────────┐          │
│  │           多 Agent 编排器 (Orchestrator)          │          │
│  │         - 辩论  - 投票  - 共识                    │          │
│  └──────────────────────────────────────────────────┘          │
│  ┌──────────────────────────────────────────────────┐          │
│  │              消息总线 (Message Bus)               │          │
│  │         - 发布/订阅  - 请求/响应                  │          │
│  └──────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────────┐
│                     LLM 接口层 (LLM)                             │
│  ┌──────────────────────────────────────────────────┐          │
│  │              BaseLLM (抽象接口)                   │          │
│  └──────────────────────────────────────────────────┘          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ OpenAI Client│  │  Local Model │  │ Azure Client │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌────────────────────────────────────────────────┐            │
│  │  - 基础对话  - 流式对话  - 工具调用            │            │
│  │  - 速率限制  - 错误重试  - 响应解析            │            │
│  └────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                              ▲
                              │
                    ┌─────────┴─────────┐
                    │   OpenAI-兼容 API  │
                    │   (OpenAI / 本地)  │
                    └───────────────────┘
```

### 分层说明

#### 1. LLM 接口层
- **职责**: 与 LLM 服务通信
- **特点**: 协议无关，支持多种 LLM 提供商
- **功能**: 基础对话、流式响应、工具调用

#### 2. Agent 层
- **职责**: 实现智能 Agent 逻辑
- **特点**: 支持多种 Agent 类型和协作模式
- **功能**: 任务规划、推理执行、多 Agent 协作

#### 3. 工具层
- **职责**: 提供 Agent 可调用的工具
- **特点**: 双协议支持（OpenAI / MCP）
- **功能**: 内置工具、领域工具、自定义工具

#### 4. 领域增强层
- **职责**: 提供固废管理领域知识
- **特点**: 专业知识深度集成
- **功能**: 知识库、术语库、标准库、优化提示词

#### 5. 工作流层
- **职责**: 提供预定义工作流模板
- **特点**: 步骤化、可复用
- **功能**: 科研、报告、分析、编码工作流

#### 6. 应用层
- **职责**: 最终应用和接口
- **特点**: 易用、可扩展
- **功能**: CLI、测试、示例程序

---

## 模块设计

### 1. LLM 接口层设计

#### 架构模式
- **策略模式**: 不同 LLM 提供商使用不同实现策略
- **适配器模式**: 统一不同 API 的接口

#### 核心组件

```
swagent/llm/
├── base_llm.py           # 抽象基类
│   └── BaseLLM
│       ├── chat()        # 基础对话
│       ├── chat_stream() # 流式对话
│       └── __init__()    # 配置初始化
│
├── openai_client.py      # OpenAI 客户端
│   └── OpenAIClient(BaseLLM)
│       ├── chat()
│       ├── chat_stream()
│       ├── chat_with_tools()  # 工具调用
│       └── _handle_rate_limit() # 速率限制
│
└── config.py             # 配置类
    ├── LLMConfig         # LLM 配置
    └── LLMResponse       # LLM 响应
```

#### 设计要点

1. **配置驱动**: 通过 `LLMConfig` 配置所有参数
2. **统一响应**: `LLMResponse` 标准化所有响应格式
3. **错误处理**: 自动重试和降级策略
4. **速率限制**: 令牌桶算法防止 API 过载

#### 扩展点

```python
# 添加新的 LLM 提供商
class CustomLLMClient(BaseLLM):
    async def chat(self, messages, **kwargs):
        # 实现自定义逻辑
        pass
```

### 2. Agent 层设计

#### 架构模式
- **模板方法模式**: BaseAgent 定义执行框架
- **观察者模式**: MessageBus 实现消息通信
- **中介者模式**: Orchestrator 协调多 Agent

#### 核心组件

```
swagent/agent/
├── base_agent.py         # Agent 基类
│   └── BaseAgent
│       ├── execute()     # 执行任务
│       ├── chat()        # 对话接口
│       └── _process()    # 内部处理（子类实现）
│
├── planner_agent.py      # 规划 Agent
│   └── PlannerAgent(BaseAgent)
│       ├── plan()        # 制定计划
│       └── execute()     # 执行任务
│
├── react_agent.py        # ReAct Agent
│   └── ReActAgent(BaseAgent)
│       ├── execute()     # ReAct 循环
│       ├── _reason()     # 推理步骤
│       └── _act()        # 行动步骤
│
├── message_bus.py        # 消息总线
│   └── MessageBus
│       ├── publish()     # 发布消息
│       ├── subscribe()   # 订阅主题
│       └── request_response() # 请求-响应
│
└── orchestrator.py       # 编排器
    └── Orchestrator
        ├── add_agent()   # 添加 Agent
        ├── debate()      # 辩论模式
        ├── vote()        # 投票模式
        └── consensus()   # 共识模式
```

#### 消息总线架构

```
┌─────────────────────────────────────────────────┐
│              Message Bus (消息总线)              │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │        Topic Subscriptions (主题订阅)     │ │
│  │  "task.request" -> [Agent1, Agent2]      │ │
│  │  "data.update"  -> [Agent3]              │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │      Message Queue (消息队列)            │ │
│  │  FIFO, 异步处理                          │ │
│  └───────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
         ▲                           │
         │ publish()                 │ deliver()
         │                           ▼
    ┌─────────┐                ┌─────────┐
    │ Agent 1 │                │ Agent 2 │
    │ (发布者)│                │ (订阅者)│
    └─────────┘                └─────────┘
```

#### 多 Agent 协作模式

**1. 辩论模式 (Debate)**
```
Round 1: Agent1 提出观点 → Agent2 反驳 → Agent3 评论
Round 2: Agent1 回应 → Agent2 补充 → Agent3 总结
...
Result: 综合所有观点形成结论
```

**2. 投票模式 (Vote)**
```
Question: 应该选择哪种处理方式？
Agent1 → 选项A (理由...)
Agent2 → 选项B (理由...)
Agent3 → 选项A (理由...)
Result: 选项A 获胜 (2票)
```

**3. 共识模式 (Consensus)**
```
Round 1: 各 Agent 提出初步方案
Round 2: 讨论差异，调整方案
Round 3: 达成共识或投票决定
Result: 最终统一方案
```

### 3. 工具层设计

#### 架构模式
- **注册表模式**: ToolRegistry 管理所有工具
- **适配器模式**: 支持多种工具调用协议
- **策略模式**: 不同工具不同执行策略

#### 核心组件

```
swagent/tools/
├── base_tool.py          # 工具基类
│   ├── BaseTool
│   │   ├── execute()     # 执行工具
│   │   ├── validate_parameters()  # 参数验证
│   │   └── _create_schema()  # 创建模式（子类实现）
│   │
│   ├── ToolSchema        # 工具模式定义
│   │   ├── to_openai_function()  # 转 OpenAI 格式
│   │   └── to_mcp_tool()         # 转 MCP 格式
│   │
│   └── ToolResult        # 执行结果
│
├── tool_registry.py      # 工具注册中心
│   └── ToolRegistry
│       ├── register()    # 注册工具
│       ├── get_tool()    # 获取工具
│       ├── execute_tool() # 执行工具
│       ├── to_openai_functions()  # 批量转换
│       └── to_mcp_tools()         # 批量转换
│
├── builtin/              # 内置工具
│   ├── code_executor.py  # 代码执行
│   ├── file_handler.py   # 文件处理
│   └── web_search.py     # 网络搜索
│
└── domain/               # 领域工具
    ├── emission_calculator.py  # 排放计算
    ├── lca_analyzer.py         # LCA 分析
    └── visualizer.py           # 数据可视化
```

#### 双协议支持设计

```python
# 工具定义
class EmissionCalculator(BaseTool):
    def _create_schema(self):
        return ToolSchema(
            name="emission_calculator",
            description="计算温室气体排放",
            parameters=[...],
            category="domain"
        )

# 自动转换为 OpenAI Function Calling 格式
openai_format = {
    "type": "function",
    "function": {
        "name": "emission_calculator",
        "description": "计算温室气体排放",
        "parameters": {
            "type": "object",
            "properties": {...},
            "required": [...]
        }
    }
}

# 自动转换为 MCP 格式
mcp_format = {
    "name": "emission_calculator",
    "description": "计算温室气体排放",
    "inputSchema": {
        "type": "object",
        "properties": {...},
        "required": [...]
    }
}
```

#### 工具执行流程

```
┌──────────────┐
│ Agent 请求   │
│ 调用工具     │
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│ ToolRegistry             │
│ 1. 查找工具              │
│ 2. 验证参数              │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Tool.execute()           │
│ 1. 执行业务逻辑          │
│ 2. 错误处理              │
│ 3. 返回 ToolResult       │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ 返回结果给 Agent         │
│ - success: bool          │
│ - data: Any              │
│ - error: Optional[str]   │
└──────────────────────────┘
```

### 4. 领域增强层设计

#### 架构模式
- **仓储模式**: 知识库作为数据仓储
- **单例模式**: 全局知识库实例
- **策略模式**: 不同查询策略

#### 核心组件

```
swagent/domain/
├── data/                 # 领域数据 (JSON)
│   ├── waste_categories.json     # 废物分类
│   ├── treatment_methods.json    # 处理方法
│   ├── terminology.json          # 术语库
│   └── standards.json            # 标准规范
│
├── knowledge_base.py     # 知识库
│   └── KnowledgeBase
│       ├── get_waste_category()  # 查询废物类别
│       ├── get_treatment_method() # 查询处理方法
│       ├── search_by_keyword()    # 关键词搜索
│       └── compare_treatments()   # 比较处理方式
│
├── terminology.py        # 术语库
│   └── TerminologyDB
│       ├── translate()           # 翻译术语
│       ├── expand_abbreviation() # 展开缩写
│       └── explain_term()        # 解释术语
│
├── standards.py          # 标准库
│   └── StandardsDB
│       ├── get_standard()        # 查询标准
│       ├── get_policy()          # 查询政策
│       └── get_compliance_requirements() # 合规要求
│
└── prompts.py            # 领域提示词
    └── DomainPrompts
        ├── get_system_prompt()   # 获取系统提示词
        └── create_xxx_prompt()   # 创建特定提示词
```

#### 知识库数据结构

```json
{
  "waste_categories": {
    "municipal_solid_waste": {
      "name": "城市固体废物",
      "subcategories": {
        "food_waste": {
          "name": "厨余垃圾",
          "composition": ["碳水化合物", "蛋白质", ...],
          "suitable_treatments": ["composting", "anaerobic_digestion"],
          "characteristics": {...}
        }
      }
    }
  },
  "treatment_methods": {
    "incineration": {
      "name": "焚烧",
      "types": {
        "wte": {
          "name": "垃圾焚烧发电",
          "temperature": "850-1100°C",
          "advantages": [...],
          "disadvantages": [...]
        }
      }
    }
  }
}
```

#### 查询策略

**1. 直接查询**
```python
kb.get_waste_category('food_waste')  # 精确匹配
```

**2. 关键词搜索**
```python
kb.search_by_keyword('回收', search_in='all')  # 全文搜索
```

**3. 比较查询**
```python
kb.compare_treatments('food_waste')  # 比较多种处理方式
```

### 5. 工作流层设计

#### 架构模式
- **责任链模式**: 步骤顺序执行
- **策略模式**: 不同工作流不同策略
- **模板方法模式**: BaseWorkflow 定义框架

#### 核心组件

```
swagent/workflows/
├── base_workflow.py      # 工作流基类
│   ├── WorkflowStep      # 步骤定义
│   ├── WorkflowContext   # 上下文
│   ├── WorkflowResult    # 结果
│   └── BaseWorkflow      # 基类
│       ├── add_step()    # 添加步骤
│       ├── execute()     # 执行工作流
│       └── _setup_steps() # 设置步骤（子类实现）
│
├── research_workflow.py  # 科研工作流
├── report_workflow.py    # 报告工作流
├── analysis_workflow.py  # 分析工作流
├── coding_workflow.py    # 编码工作流
│
└── workflow_manager.py   # 工作流管理器
    └── WorkflowManager
        ├── register()    # 注册工作流
        ├── get_workflow() # 获取工作流
        ├── execute_workflow() # 执行工作流
        └── get_workflow_by_purpose() # 推荐工作流
```

#### 工作流执行流程

```
┌─────────────────────────────────────────────────────┐
│ 1. 初始化                                            │
│    - 创建 WorkflowContext                           │
│    - 加载初始数据                                    │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 2. 步骤循环                                          │
│    For each step:                                   │
│    ┌─────────────────────────────────────────────┐ │
│    │ 2.1 验证依赖                                 │ │
│    │     - 检查 required_inputs 是否满足         │ │
│    └─────────────────────────────────────────────┘ │
│    ┌─────────────────────────────────────────────┐ │
│    │ 2.2 执行步骤                                 │ │
│    │     - 调用 execute_func(context)            │ │
│    │     - 支持重试（max_retries）               │ │
│    └─────────────────────────────────────────────┘ │
│    ┌─────────────────────────────────────────────┐ │
│    │ 2.3 更新上下文                               │ │
│    │     - 将 outputs 写入 context               │ │
│    └─────────────────────────────────────────────┘ │
│    ┌─────────────────────────────────────────────┐ │
│    │ 2.4 错误处理                                 │ │
│    │     - stop_on_error=True: 中断              │ │
│    │     - stop_on_error=False: 继续             │ │
│    └─────────────────────────────────────────────┘ │
└─────────────────┬───────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────┐
│ 3. 返回结果                                          │
│    - WorkflowResult                                 │
│    - 包含所有步骤结果和最终上下文                     │
└─────────────────────────────────────────────────────┘
```

#### 上下文传递

```python
# 步骤 1: 文献调研
async def literature_review(context: WorkflowContext):
    topic = context.get('research_topic')
    # ... 执行文献调研
    return {
        'literature_summary': "...",
        'key_papers': [...]
    }

# 步骤 2: 研究设计（依赖步骤 1）
async def research_design(context: WorkflowContext):
    # 从上下文获取步骤 1 的输出
    literature = context.get('literature_summary')
    papers = context.get('key_papers')
    # ... 基于文献设计研究
    return {
        'research_design': "...",
        'methodology': "..."
    }
```

---

## 数据流

### 1. 单 Agent 执行流程

```
User Input
    │
    ▼
┌──────────────────────┐
│ Agent.execute(task)  │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ 构建 messages        │
│ [system, user]       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ LLM.chat(messages)   │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│ LLM Response         │
│ - content            │
│ - tool_calls?        │
└──────────┬───────────┘
           │
           ▼
    ┌──────────┐
    │ 有工具调用? │
    └──┬────┬───┘
      Yes  No
       │    └─────────────┐
       ▼                  │
┌──────────────────────┐ │
│ Tool.execute()       │ │
│ 获取工具结果          │ │
└──────────┬───────────┘ │
           │              │
           ▼              │
┌──────────────────────┐ │
│ 添加 tool_result     │ │
│ 到 messages          │ │
└──────────┬───────────┘ │
           │              │
           └───► LLM ◄────┘
                 (再次调用)
                    │
                    ▼
                Final Response
                    │
                    ▼
                User Output
```

### 2. 多 Agent 协作流程（辩论模式）

```
┌──────────────────────────────────────────────────┐
│ Orchestrator.debate(topic, rounds=2)             │
└──────────────────┬───────────────────────────────┘
                   │
           ┌───────┴────────┐
           ▼                ▼                ▼
      ┌────────┐       ┌────────┐      ┌────────┐
      │ Agent1 │       │ Agent2 │      │ Agent3 │
      └───┬────┘       └───┬────┘      └───┬────┘
          │                │                │
   Round 1: 提出观点
          │                │                │
          ▼                ▼                ▼
     "观点A"          "观点B"          "观点C"
          │                │                │
          └────────┬───────┴────────┬───────┘
                   ▼
         ┌──────────────────┐
         │ Message Bus      │
         │ 收集所有观点      │
         └─────────┬────────┘
                   │
   Round 2: 基于前轮观点回应
                   │
           ┌───────┴────────┐
           ▼                ▼                ▼
      ┌────────┐       ┌────────┐      ┌────────┐
      │ Agent1 │       │ Agent2 │      │ Agent3 │
      │ 回应B,C│       │ 回应A,C│      │ 回应A,B│
      └───┬────┘       └───┬────┘      └───┬────┘
          │                │                │
          └────────┬───────┴────────┬───────┘
                   ▼
         ┌──────────────────┐
         │ LLM 总结所有观点  │
         │ 形成最终结论      │
         └─────────┬────────┘
                   │
                   ▼
              Final Result
```

### 3. 工作流执行数据流

```
Initial Context
    │
    ▼
┌─────────────────────────────────────────────┐
│ Step 1: literature_review                   │
│ Input:  research_topic                      │
│ Output: literature_summary, key_papers      │
└─────────────────┬───────────────────────────┘
                  │
        Context.update(outputs)
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ Step 2: research_design                     │
│ Input:  literature_summary, key_papers      │
│ Output: research_design, methodology        │
└─────────────────┬───────────────────────────┘
                  │
        Context.update(outputs)
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ Step 3: data_collection                     │
│ Input:  research_design, methodology        │
│ Output: collected_data, data_sources        │
└─────────────────┬───────────────────────────┘
                  │
                 ...
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ Step N: final_step                          │
│ Input:  all previous outputs                │
│ Output: final_conclusions                   │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
            WorkflowResult
       (包含完整的 Context)
```

---

## 扩展性设计

### 1. 添加新的 LLM 提供商

```python
# 1. 继承 BaseLLM
from swagent.llm import BaseLLM, LLMResponse

class CustomLLMClient(BaseLLM):
    async def chat(self, messages, **kwargs):
        # 实现自定义 API 调用
        response = await self._call_custom_api(messages)
        return LLMResponse(
            content=response['text'],
            usage=response['usage']
        )

    async def chat_stream(self, messages, **kwargs):
        # 实现流式响应
        async for chunk in self._stream_custom_api(messages):
            yield chunk

# 2. 使用自定义客户端
config = LLMConfig(
    provider="custom",
    model="custom-model",
    api_key="your_key",
    base_url="https://custom-api.com/v1"
)
llm = CustomLLMClient(config)
```

### 2. 添加新的 Agent 类型

```python
# 1. 继承 BaseAgent
from swagent.agent import BaseAgent

class CustomAgent(BaseAgent):
    async def execute(self, task, context=None):
        # 实现自定义执行逻辑
        # 1. 分析任务
        analysis = await self._analyze_task(task)

        # 2. 执行自定义逻辑
        result = await self._custom_logic(analysis, context)

        # 3. 返回结果
        return result

    async def _analyze_task(self, task):
        # 自定义任务分析
        pass

    async def _custom_logic(self, analysis, context):
        # 自定义执行逻辑
        pass

# 2. 使用自定义 Agent
agent = CustomAgent("custom_agent", llm=llm)
result = await agent.execute("任务描述")
```

### 3. 添加新的工具

```python
# 1. 继承 BaseTool
from swagent.tools import BaseTool, ToolSchema, ToolParameter, ToolResult

class CustomTool(BaseTool):
    def _create_schema(self) -> ToolSchema:
        return ToolSchema(
            name="custom_tool",
            description="自定义工具描述",
            parameters=[
                ToolParameter(
                    name="param1",
                    type="string",
                    description="参数1描述",
                    required=True
                )
            ],
            category="custom"
        )

    async def execute(self, **kwargs) -> ToolResult:
        # 实现工具逻辑
        param1 = kwargs.get('param1')

        try:
            # 执行操作
            result_data = await self._do_something(param1)

            return ToolResult(
                success=True,
                data=result_data
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )

# 2. 注册工具
from swagent.tools import get_global_registry

registry = get_global_registry()
registry.register(CustomTool())

# 3. 使用工具
result = await registry.execute_tool("custom_tool", param1="value")
```

### 4. 添加新的工作流

```python
# 1. 继承 BaseWorkflow
from swagent.workflows import BaseWorkflow, WorkflowContext

class CustomWorkflow(BaseWorkflow):
    def __init__(self):
        super().__init__(
            name="自定义工作流",
            description="工作流描述"
        )

    def _setup_steps(self):
        # 添加步骤
        self.add_step(
            name="step1",
            description="步骤1描述",
            execute_func=self._step1,
            required_inputs=["input1"],
            outputs=["output1"]
        )

        self.add_step(
            name="step2",
            description="步骤2描述",
            execute_func=self._step2,
            required_inputs=["output1"],
            outputs=["final_result"]
        )

    async def _step1(self, context: WorkflowContext):
        input1 = context.get('input1')
        # 执行步骤1逻辑
        return {'output1': result}

    async def _step2(self, context: WorkflowContext):
        output1 = context.get('output1')
        # 执行步骤2逻辑
        return {'final_result': result}

# 2. 注册工作流
from swagent.workflows import get_workflow_manager

manager = get_workflow_manager()
manager.register('custom', CustomWorkflow)

# 3. 执行工作流
result = await manager.execute_workflow(
    'custom',
    initial_context={'input1': 'value'}
)
```

### 5. 扩展领域知识库

```python
# 1. 添加新的 JSON 数据文件
# swagent/domain/data/custom_knowledge.json
{
    "custom_data": {
        "item1": {...},
        "item2": {...}
    }
}

# 2. 创建自定义知识库类
from swagent.domain import KnowledgeBase

class CustomKnowledgeBase:
    def __init__(self):
        # 加载自定义数据
        self.data = self._load_custom_data()

    def get_custom_item(self, item_id):
        return self.data.get(item_id)

    def search_custom(self, keyword):
        # 实现搜索逻辑
        pass

# 3. 使用自定义知识库
custom_kb = CustomKnowledgeBase()
item = custom_kb.get_custom_item('item1')
```

---

## 性能考虑

### 1. 异步并发

**设计原则**: 全面采用 `async/await` 实现异步操作

```python
# ✓ 并发执行多个 Agent
results = await asyncio.gather(
    agent1.execute(task1),
    agent2.execute(task2),
    agent3.execute(task3)
)

# ✓ 并发调用多个工具
tool_results = await asyncio.gather(
    tool1.execute(**params1),
    tool2.execute(**params2)
)
```

### 2. 速率限制

**令牌桶算法**: 防止 API 过载

```python
class RateLimiter:
    def __init__(self, rate: int, per: float):
        self.rate = rate      # 每时间段允许的请求数
        self.per = per        # 时间段（秒）
        self.allowance = rate
        self.last_check = time.time()

    async def acquire(self):
        current = time.time()
        time_passed = current - self.last_check
        self.last_check = current
        self.allowance += time_passed * (self.rate / self.per)

        if self.allowance > self.rate:
            self.allowance = self.rate

        if self.allowance < 1.0:
            sleep_time = (1.0 - self.allowance) * (self.per / self.rate)
            await asyncio.sleep(sleep_time)
            self.allowance = 0.0
        else:
            self.allowance -= 1.0
```

### 3. 缓存策略

**知识库缓存**: 避免重复加载

```python
# 单例模式 + 懒加载
_knowledge_base_instance = None

def get_knowledge_base():
    global _knowledge_base_instance
    if _knowledge_base_instance is None:
        _knowledge_base_instance = KnowledgeBase()
    return _knowledge_base_instance
```

### 4. 错误重试

**指数退避**: 失败时逐渐增加重试间隔

```python
async def retry_with_backoff(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait_time = (2 ** attempt) + random.random()
            await asyncio.sleep(wait_time)
```

### 5. 资源管理

**上下文管理器**: 自动清理资源

```python
class LLMClient:
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

# 使用
async with LLMClient(config) as client:
    response = await client.chat(messages)
# 自动清理连接
```

### 6. 内存优化

**流式处理**: 处理大型响应时避免一次性加载

```python
# ✓ 流式处理
async for chunk in llm.chat_stream(messages):
    process(chunk)  # 逐块处理，内存占用小

# ✗ 一次性加载（大响应时内存占用高）
response = await llm.chat(messages)
process(response.content)
```

---

## 安全考虑

### 1. API 密钥管理

```python
# ✓ 使用环境变量
import os
api_key = os.getenv('OPENAI_API_KEY')

# ✓ 使用 .env 文件（不提交到版本控制）
from dotenv import load_dotenv
load_dotenv()

# ✗ 硬编码（不安全）
api_key = "sk-..."  # 永远不要这样做
```

### 2. 输入验证

```python
def validate_parameters(self, **kwargs):
    """验证工具参数"""
    for param in self.schema.parameters:
        if param.required and param.name not in kwargs:
            return False, f"Missing required parameter: {param.name}"

        if param.name in kwargs:
            value = kwargs[param.name]
            # 类型检查
            if not self._check_type(value, param.type):
                return False, f"Invalid type for {param.name}"
            # 枚举检查
            if param.enum and value not in param.enum:
                return False, f"Invalid value for {param.name}"

    return True, None
```

### 3. 代码执行安全

```python
# 沙箱执行
import subprocess

async def execute_code(code, language="python", timeout=30):
    if language == "python":
        # 限制可用模块
        safe_globals = {"__builtins__": __builtins__}
        # 使用 exec 而不是 eval
        exec(code, safe_globals)
    elif language == "shell":
        # 使用 subprocess 隔离
        result = subprocess.run(
            code,
            shell=True,
            capture_output=True,
            timeout=timeout,
            check=False
        )
```

---

## 未来架构演进

### Phase 6 规划

1. **多模型支持**
   - 集成 Anthropic Claude、Cohere 等模型
   - 模型路由和负载均衡

2. **持久化存储**
   - 对话历史存储（SQLite/PostgreSQL）
   - 知识库版本管理
   - Agent 状态持久化

3. **Web UI**
   - FastAPI 后端
   - React 前端
   - WebSocket 实时通信

4. **API 服务**
   - RESTful API
   - GraphQL 支持
   - API 认证和限流

5. **监控和日志**
   - Prometheus 指标收集
   - ELK 日志聚合
   - 分布式追踪（Jaeger）

---

## 总结

SWAgent 的架构设计遵循以下核心理念：

1. **分层清晰**: 各层职责明确，降低耦合
2. **可扩展性**: 易于添加新功能和集成新服务
3. **异步优先**: 提升性能和响应能力
4. **领域驱动**: 深度集成固废管理知识
5. **协议无关**: 支持多种 LLM 和工具协议

这种架构设计确保了系统的可维护性、可扩展性和专业性，为固废管理智能化提供了坚实的技术基础。
