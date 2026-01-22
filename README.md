# Wuyu-Agent - 专业多智能体协作系统

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Wuyu-Agent** 是一个强大的多智能体协作系统，专为解决复杂的研究、企业和政府问题而设计。系统集成了先进的LLM技术、多Agent协作框架、专业工具集和领域知识库，能够高效完成复杂问题分析、长篇报告撰写等专业任务。

## 🎯 核心应用场景

### 1. 专业多智能体问题解决系统
通过多个专业Agent的协作，深度分析和解决研究、企业和政府领域的复杂问题。

### 2. 垂域长文报告生成系统
自动化生成高质量的专业分析报告、研究报告、技术评估等长篇文档。

## ✨ 主要特性

### 🤖 智能Agent系统
- **多种Agent类型**：PlannerAgent（规划）、ReActAgent（推理-行动）
- **多Agent协作**：支持辩论、投票、共识等协作模式
- **消息总线**：统一的Agent间通信机制
- **速率限制**：防止API过载的智能限流

### 🛠️ 强大的工具系统
- **双协议支持**：同时支持OpenAI Function Calling和MCP协议
- **内置工具**：代码执行、文件处理、网络搜索
- **领域工具**：排放计算、LCA分析、数据可视化
- **工具注册中心**：灵活的工具管理和调用

### 📚 专业领域知识库
- **固废知识库**：废物分类、处理方法、废物层级
- **专业术语库**：60+ 术语，中英互译，缩写展开
- **标准规范库**：30+ 国家/国际标准、法规政策
- **领域提示词**：8种专业场景的优化提示词

### 🔄 预定义工作流
- **科研工作流**：文献调研 → 研究设计 → 数据分析 → 论文撰写
- **报告工作流**：需求分析 → 数据收集 → 内容撰写 → 质量检查
- **分析工作流**：数据导入 → 清洗 → 统计分析 → 可视化
- **编码工作流**：需求分析 → 设计 → 编码 → 测试 → 文档

### 🔌 灵活的LLM集成
- **多模型支持**：OpenAI、本地模型、Azure
- **自定义base_url**：支持本地部署的兼容API
- **流式响应**：支持流式对话
- **Function Calling**：原生支持工具调用

### 📊 StateGraph 工作流引擎
- **状态图工作流**：类似 LangGraph 的声明式工作流定义
- **多种节点类型**：支持同步/异步函数、装饰器模式
- **灵活的边定义**：固定边、条件边、并行边
- **循环支持**：支持迭代处理模式
- **状态持久化**：检查点保存和恢复
- **错误处理**：可配置的重试策略和退避算法

## 🏗️ 架构概览

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      应用层 (Application)                    │
│            CLI / Examples / Interactive Agent                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     工作流层 (Workflow)                      │
│     StateGraph Engine │ Research │ Report │ Analysis        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Agent层 (Multi-Agent)                     │
│   BaseAgent │ ReActAgent │ PlannerAgent │ Orchestrator      │
│                    MessageBus (通信)                         │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌───────────────────┐ ┌─────────────┐ ┌─────────────────────┐
│    工具层 (Tools)  │ │ 领域层      │ │   LLM接口层          │
│ ToolRegistry      │ │ Knowledge   │ │ OpenAI/Local/Azure  │
│ Builtin/Domain    │ │ Terminology │ │ Function Calling    │
│ OpenAI+MCP协议    │ │ Standards   │ │ Streaming           │
└───────────────────┘ └─────────────┘ └─────────────────────┘
```

### 核心组件说明

| 层级 | 模块 | 职责 |
|------|------|------|
| LLM接口层 | `llm/` | 统一的LLM调用接口，支持多种模型 |
| Agent层 | `agent/` | Agent生命周期、多Agent协作 |
| 工具层 | `tools/` | 工具注册、执行、双协议支持 |
| 领域层 | `domain/` | 专业知识库、术语、标准 |
| 工作流层 | `workflows/`, `stategraph/` | 预定义流程、状态图引擎 |

### 数据流

```
用户输入 → Agent → LLM调用 → 工具调用(可选) → 响应生成 → 用户输出
              ↓
         领域知识增强
```

### 目录结构

```
swagent/                    # 主包目录
├── __init__.py
├── agents/                 # Agent实现
│   ├── planner_agent.py        # 规划Agent
│   └── react_agent.py          # ReAct Agent
│
├── core/                   # 核心模块
│   ├── base_agent.py           # Agent基类
│   ├── communication.py        # 通信模块
│   ├── context.py              # 上下文管理
│   ├── message.py              # 消息定义
│   └── orchestrator.py         # 多Agent编排器
│
├── llm/                    # LLM接口层
│   ├── base_llm.py             # LLM基类
│   └── openai_client.py        # OpenAI客户端
│
├── tools/                  # 工具系统
│   ├── base_tool.py            # 工具基类
│   ├── tool_registry.py        # 工具注册中心
│   ├── builtin/                # 内置工具
│   │   ├── code_executor.py        # 代码执行
│   │   ├── file_handler.py         # 文件处理
│   │   └── web_search.py           # 网络搜索
│   └── domain/                 # 领域工具
│       ├── emission_calculator.py  # 排放计算
│       ├── imagery_tool.py         # 卫星影像
│       ├── lca_analyzer.py         # LCA分析
│       ├── location_tool.py        # 位置服务
│       ├── visualizer.py           # 数据可视化
│       └── weather_tool.py         # 天气查询
│
├── domain/                 # 领域增强
│   ├── knowledge_base.py       # 知识库
│   ├── terminology.py          # 术语库
│   ├── standards.py            # 标准库
│   └── prompts.py              # 领域提示词
│
├── workflows/              # 工作流模板
│   ├── base_workflow.py        # 工作流基类
│   ├── workflow_manager.py     # 工作流管理器
│   ├── research_workflow.py    # 科研工作流
│   ├── report_workflow.py      # 报告工作流
│   ├── analysis_workflow.py    # 分析工作流
│   └── coding_workflow.py      # 编码工作流
│
├── stategraph/             # StateGraph 工作流引擎
│   ├── state.py                # 状态管理
│   ├── node.py                 # 节点定义
│   ├── edge.py                 # 边定义
│   ├── graph.py                # 图核心
│   ├── persistence.py          # 状态持久化
│   ├── errors.py               # 错误处理
│   └── integrations/           # 集成模块
│       ├── llm_nodes.py            # LLM 节点
│       ├── agent_nodes.py          # Agent 节点
│       └── tool_nodes.py           # Tool 节点
│
└── utils/                  # 工具模块
    ├── config.py               # 配置管理
    └── logger.py               # 日志模块
```

## 📦 安装

### 环境要求
- Python 3.8+
- pip

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/xxy33/Wuyu-agent.git
cd Wuyu-agent

# 安装依赖
pip install -r requirements.txt

# （可选）安装可选依赖
pip install matplotlib  # 用于数据可视化
```

### 配置

创建 `.env` 文件并配置：

```env
# OpenAI配置
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1  # 或你的自定义URL

# 模型配置
DEFAULT_MODEL=gpt-4
DEFAULT_TEMPERATURE=0.7
```

## 🚀 快速开始

### 1. 基础Agent使用

```python
import asyncio
from swagent.agent import ReActAgent
from swagent.llm import OpenAIClient, LLMConfig

# 配置LLM
config = LLMConfig(
    provider="openai",
    model="gpt-4",
    api_key="your_api_key",
    base_url="https://api.openai.com/v1"
)
llm = OpenAIClient(config)

# 创建Agent
agent = ReActAgent("助手", llm=llm)

# 执行任务
async def main():
    result = await agent.execute("帮我分析一下塑料回收的环境效益")
    print(result)

asyncio.run(main())
```

### 2. 使用工具系统

```python
from swagent.tools import ToolRegistry
from swagent.tools.domain import EmissionCalculator

# 创建工具注册中心
registry = ToolRegistry()

# 注册工具
calculator = EmissionCalculator()
registry.register(calculator)

# 使用工具
result = await registry.execute_tool(
    "emission_calculator",
    waste_type="food_waste",
    treatment_method="composting",
    quantity=100
)

print(f"碳排放: {result.data['total_emission_kgCO2e']} kg CO2e")
```

### 3. 使用领域知识库

```python
from swagent.domain import get_knowledge_base, get_terminology_db

# 知识库查询
kb = get_knowledge_base()
food_waste = kb.get_waste_category('food_waste')
print(f"适合的处理方式: {food_waste['suitable_treatments']}")

# 术语翻译
term_db = get_terminology_db()
translation = term_db.translate('MSW', 'zh')
print(f"MSW = {translation}")
```

### 4. 执行工作流

```python
from swagent.workflows import get_workflow_manager

# 获取工作流管理器
manager = get_workflow_manager()

# 执行科研工作流
result = await manager.execute_workflow(
    'research',
    initial_context={
        'research_topic': '固体废物厌氧消化技术',
        'keywords': ['厌氧消化', '沼气', '有机废物']
    }
)

print(f"完成率: {result.completion_rate * 100}%")
```

### 6. StateGraph 工作流

```python
import asyncio
from swagent.stategraph import StateGraph, START, END
from typing import TypedDict

# 定义状态类型
class PipelineState(TypedDict):
    input: str
    processed: str
    result: str

# 创建图
graph = StateGraph(PipelineState)

# 定义节点
@graph.node()
async def preprocess(state: PipelineState) -> dict:
    return {"processed": state["input"].strip().lower()}

@graph.node()
async def analyze(state: PipelineState) -> dict:
    return {"result": f"分析结果: {state['processed']}"}

# 设置流程
graph.set_entry_point("preprocess")
graph.add_edge("preprocess", "analyze")
graph.set_exit_point("analyze")

# 编译并执行
app = graph.compile()

async def main():
    result = await app.invoke({"input": "  HELLO WORLD  "})
    print(result.state["result"])  # "分析结果: hello world"

asyncio.run(main())
```

### 7. 交互式 GIS Agent

系统提供了一个终端交互式 GIS Agent，可以查询天气和获取卫星影像。

#### 快速启动

```bash
# 方式 1: 使用启动脚本
./start_gis_agent.sh

# 方式 2: 直接运行
python examples/interactive_gis_agent.py
```

#### 功能特性

- **天气查询**: 查询全球任意位置的实时天气数据
- **卫星影像**: 获取 Google Earth、吉林一号、Sentinel-2 卫星图像
- **双模式支持**: 智能模式（LLM）和简化模式（关键词匹配）
- **灵活输入**: 支持城市名称和坐标格式

#### 使用示例

**城市查询**:
```
👤 您: 查询北京的天气

🤖 Agent:
📍 北京 当前天气:
   🌡️  温度: -7.5°C
   💧 湿度: 18%
   🌧️  降水: 0.0 mm
   💨 风速: 12.5 km/h
```

**坐标查询**:
```
👤 您: 查询(51.30, 00.07)这个位置的天气

🤖 Agent:
📍 坐标 (51.30, 0.07) 当前天气:
   🌡️  温度: 7.9°C
   💧 湿度: 95%
   🌧️  降水: 0.0 mm
   💨 风速: 18.5 km/h
```

**影像下载**:
```
👤 您: 下载上海的卫星影像

🤖 Agent:
📍 上海 卫星影像:
   🗺️  数据源: google
   📐 影像尺寸: 1000x1000 像素
   💾 已保存到: ./satellite_images/上海_satellite.png
```

#### 支持的位置

- **预定义城市**: 北京、上海、广州、深圳、成都、杭州
- **坐标格式**: `(纬度, 经度)` 例如 `(51.30, 00.07)`
- **全球覆盖**: 支持任意经纬度坐标

#### 相关文档

- [交互式 Agent 详细指南](docs/INTERACTIVE_GIS_AGENT.md)
- [快速开始](INTERACTIVE_AGENT_QUICKSTART.md)
- [坐标支持说明](COORDINATE_SUPPORT_UPDATE.md)
- [GIS 工具文档](docs/GIS_TOOLS.md)

## 📖 核心功能

### Agent系统

```python
# 1. PlannerAgent - 任务规划
from swagent.agent import PlannerAgent

planner = PlannerAgent("规划师", llm=llm)
plan = await planner.plan("设计一个厨余垃圾处理方案")

# 2. ReActAgent - 推理-行动循环
from swagent.agent import ReActAgent

react = ReActAgent("分析师", llm=llm)
result = await react.execute("分析填埋和焚烧的优缺点")

# 3. 多Agent协作
from swagent.agent import Orchestrator

orchestrator = Orchestrator(llm=llm)
orchestrator.add_agent(planner)
orchestrator.add_agent(react)

result = await orchestrator.debate(
    "应该优先选择填埋还是焚烧？",
    rounds=2
)
```

### 工具调用

```python
# 1. 排放计算
from swagent.tools.domain import EmissionCalculator

calculator = EmissionCalculator()
result = await calculator.execute(
    waste_type="plastic",
    treatment_method="recycling",
    quantity=100,
    include_transport=True,
    transport_distance=20
)

# 2. LCA分析
from swagent.tools.domain import LCAAnalyzer

analyzer = LCAAnalyzer()
result = await analyzer.execute(
    treatment_method="recycling",
    quantity=100,
    impact_categories=["climate_change", "energy_consumption"]
)

# 3. 数据可视化
from swagent.tools.domain import Visualizer

visualizer = Visualizer()
result = await visualizer.execute(
    chart_type="bar",
    data={"labels": ["填埋", "焚烧", "回收"], "values": [580, 450, -800]},
    title="不同处理方式的碳排放"
)
```

### 领域知识

```python
# 1. 知识库查询
from swagent.domain import get_knowledge_base

kb = get_knowledge_base()

# 获取处理方法
method = kb.get_treatment_method('anaerobic_digestion')
print(method['advantages'])

# 比较处理方式
comparison = kb.compare_treatments('food_waste')

# 搜索
results = kb.search_by_keyword('回收')

# 2. 术语库
from swagent.domain import get_terminology_db

term_db = get_terminology_db()

# 翻译术语
term_db.translate('WTE', 'zh')  # 垃圾焚烧发电

# 展开缩写
term_db.expand_abbreviation('LCA', 'zh')  # 生命周期评估

# 解释术语
explanation = term_db.explain_term('biogas', detailed=True)

# 3. 标准规范
from swagent.domain import get_standards_db

std_db = get_standards_db()

# 查询标准
standard = std_db.get_standard('GB18485-2014')
print(standard['key_requirements']['emission_limits'])

# 查询政策
policy = std_db.get_policy('carbon_neutrality_target')

# 最佳实践
practice = std_db.get_best_practice('circular_economy')
```

### 工作流模板

```python
from swagent.workflows import (
    ResearchWorkflow,
    ReportWorkflow,
    DataAnalysisWorkflow,
    CodingWorkflow
)

# 1. 科研工作流
research_wf = ResearchWorkflow()
result = await research_wf.execute({
    'research_topic': '固废处理技术',
    'keywords': ['技术', '环境', '经济']
})

# 2. 报告工作流
report_wf = ReportWorkflow()
result = await report_wf.execute({
    'report_type': 'technical',
    'report_purpose': '年度总结'
})

# 3. 数据分析工作流
analysis_wf = DataAnalysisWorkflow()
result = await analysis_wf.execute({
    'data_source': 'data.csv',
    'file_format': 'csv'
})

# 4. 代码开发工作流
coding_wf = CodingWorkflow()
result = await coding_wf.execute({
    'feature_request': '实现资源管理API'
})
```

## 📊 示例项目

完整示例请查看 `examples/` 目录：

- `01_basic_agent_demo.py` - Agent基础使用
- `02_multi_agent_demo.py` - 多Agent协作
- `03_tool_calling_demo.py` - 工具调用演示
- `04_domain_enhancement_demo.py` - 领域增强演示

运行示例：

```bash
python examples/01_basic_agent_demo.py
```

## 🧪 测试

运行测试套件：

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定阶段测试
python tests/test_phase1_llm.py          # LLM接口层
python tests/test_phase2_agents.py       # Agent系统
python tests/test_phase3_multi_agent.py  # 多Agent协作
python tests/test_phase4_tools.py        # 工具系统
python tests/test_phase4_domain.py       # 领域增强
python tests/test_phase5_workflows.py    # 工作流模板
```

## 📚 文档

详细文档请查看 `docs/` 目录：

- [用户指南](docs/user_guide.md) - 完整使用指南
- [API参考](docs/api_reference.md) - API文档
- [架构设计](docs/architecture.md) - 系统架构说明
- [开发指南](docs/development.md) - 开发者指南
- [StateGraph 工作流引擎](docs/STATEGRAPH.md) - 状态图工作流引擎文档

## 🛣️ 路线图

### 已完成 ✅
- [x] Phase 1: LLM接口层
- [x] Phase 2: Agent基础框架
- [x] Phase 3: 多Agent协作
- [x] Phase 4: 工具系统
- [x] Phase 4: 领域增强
- [x] Phase 5: 工作流模板
- [x] Phase 6: StateGraph 工作流引擎
  - [x] 状态管理（TypedDict、合并策略）
  - [x] 节点定义（装饰器、重试、超时）
  - [x] 边定义（固定边、条件边、并行边）
  - [x] 图执行（编译、invoke、stream）
  - [x] 循环支持（最大迭代次数保护）
  - [x] 状态持久化（内存、文件）
  - [x] 错误处理（重试策略、退避算法）
  - [x] 集成模块（LLM、Agent、Tool 节点）

### 计划中 📋
- [ ] Phase 7: 高级功能
  - [ ] 多模型支持（Anthropic, Cohere等）
  - [ ] 持久化存储（对话历史、知识库更新）
  - [ ] Web UI界面
  - [ ] API服务
  - [ ] 监控和日志系统
- [ ] 性能优化
- [ ] 更多领域工具
- [ ] 更多工作流模板

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何参与项目。

### 贡献方式
1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- OpenAI - GPT模型和Function Calling
- IPCC - 温室气体排放因子数据
- ISO - LCA标准（ISO 14040/14044）
- 中国国家标准 - 固废管理标准规范

## 📞 联系方式
https://github.com/xxy33/Wuyu-agent
- 项目主页: [https://github.com/xxy33/Wuyu-agent](https://github.com/xxy33/Wuyu-agent)
- Issues: [https://github.com/xxy33/Wuyu-agent/issues](https://github.com/xxy33/Wuyu-agent/issues)

## 🌟 Star History

如果这个项目对你有帮助，请给它一个 ⭐️！
