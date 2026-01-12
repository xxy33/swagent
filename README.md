# SolidWaste-Agent (SWAgent)

> 面向固体废物领域的多智能体协作框架

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-in_development-yellow.svg)]()

## 📖 项目简介

SolidWaste-Agent (SWAgent) 是一个专门面向固体废物领域的多智能体协作框架，支持科研辅助、代码生成、报告撰写、数据分析等任务。该框架通过多个专业Agent的协作，帮助研究人员和工程师高效完成固废领域的各类工作。

### ✨ 核心特性

- 🔄 **灵活的Agent交互与通信机制** - 支持点对点、广播、发布订阅等多种通信模式
- 📝 **上下文感知与记忆管理** - 智能的上下文管理和多级记忆系统
- 🛠️ **可扩展的工具调用系统** - 内置多种工具，支持自定义扩展
- 🏭 **固废领域专业知识集成** - 包含固废分类、排放计算、LCA分析等专业工具
- 🤖 **多Agent协作编排** - 支持顺序、并行、层级等多种编排模式
- 📊 **工作流模板** - 提供科研、报告、分析等预设工作流

## 🚀 快速开始

### 环境要求

- Python 3.8+
- pip 包管理器
- OpenAI API密钥（可选，支持本地模型）

### 安装步骤

1. **克隆或下载项目**

```bash
cd c:/Users/CHENXY/Desktop/x/vscode/envagent
```

2. **创建虚拟环境（推荐）**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

3. **安装依赖**

```bash
pip install -r requirements.txt
```

4. **配置环境变量**

创建 `.env` 文件并添加API密钥：

```bash
# .env 文件
OPENAI_API_KEY=your_openai_api_key_here
```

或在系统中设置环境变量：

```bash
# Windows (CMD)
set OPENAI_API_KEY=your_openai_api_key_here

# Windows (PowerShell)
$env:OPENAI_API_KEY="your_openai_api_key_here"

# Linux/Mac
export OPENAI_API_KEY=your_openai_api_key_here
```

5. **验证安装**

```bash
python examples/01_simple_chat.py
```

## 📚 项目结构

```
envagent/
├── README.md                    # 项目说明文档（本文件）
├── INSTALLATION.md              # 详细安装配置指南
├── requirements.txt             # Python依赖包列表
├── setup.py                     # 安装配置脚本
├── config.yaml                  # 全局配置文件
├── .env.example                 # 环境变量示例
│
├── swagent/                     # 核心包
│   ├── __init__.py
│   ├── core/                    # 核心模块
│   │   ├── base_agent.py        # Agent基类
│   │   ├── message.py           # 消息系统
│   │   ├── context.py           # 上下文管理
│   │   ├── memory.py            # 记忆系统
│   │   ├── communication.py     # 通信协议
│   │   └── orchestrator.py      # 编排调度器
│   │
│   ├── agents/                  # Agent实现
│   │   ├── planner_agent.py     # 规划Agent
│   │   ├── coder_agent.py       # 代码Agent
│   │   ├── writer_agent.py      # 写作Agent
│   │   ├── researcher_agent.py  # 研究Agent
│   │   ├── data_agent.py        # 数据分析Agent
│   │   └── reviewer_agent.py    # 审核Agent
│   │
│   ├── tools/                   # 工具系统
│   │   ├── base_tool.py         # 工具基类
│   │   ├── tool_registry.py     # 工具注册
│   │   ├── builtin/             # 内置工具
│   │   └── domain/              # 领域工具
│   │
│   ├── domain/                  # 固废领域模块
│   │   ├── knowledge_base.py    # 知识库
│   │   ├── terminology.py       # 术语库
│   │   └── data/                # 领域数据
│   │
│   ├── llm/                     # LLM接口层
│   │   ├── base_llm.py          # LLM基类
│   │   ├── openai_client.py     # OpenAI接口
│   │   └── prompt_manager.py    # Prompt管理
│   │
│   └── utils/                   # 工具函数
│       ├── logger.py            # 日志系统
│       └── config.py            # 配置管理
│
├── workflows/                   # 工作流定义
│   ├── research_workflow.py     # 科研工作流
│   ├── report_workflow.py       # 报告工作流
│   └── analysis_workflow.py     # 分析工作流
│
├── examples/                    # 示例代码
│   ├── 01_simple_chat.py        # 简单对话
│   ├── 02_code_generation.py    # 代码生成
│   ├── 03_report_writing.py     # 报告撰写
│   ├── 04_multi_agent.py        # 多Agent协作
│   └── 05_domain_analysis.py    # 领域分析
│
├── tests/                       # 测试代码
│   ├── test_agents.py
│   ├── test_tools.py
│   └── test_workflows.py
│
└── docs/                        # 文档
    ├── architecture.md          # 架构设计
    ├── api_reference.md         # API参考
    ├── development_guide.md     # 开发指南
    └── domain_knowledge.md      # 领域知识说明
```

## 💡 使用示例

### 1. 简单对话

```python
import asyncio
from swagent.agents.planner_agent import PlannerAgent
from swagent.core.message import Message, MessageType

async def main():
    # 创建Agent
    agent = PlannerAgent()
    
    # 创建消息
    message = Message(
        sender="user",
        sender_name="用户",
        content="请分析城市生活垃圾焚烧的碳排放计算方法",
        msg_type=MessageType.REQUEST
    )
    
    # 运行Agent
    response = await agent.run(message)
    print(response.content)

asyncio.run(main())
```

### 2. 多Agent协作

```python
import asyncio
from swagent.core.orchestrator import Orchestrator, TaskDefinition
from swagent.agents.planner_agent import PlannerAgent

async def main():
    # 创建编排器
    orchestrator = Orchestrator()
    
    # 注册Agent
    planner = PlannerAgent()
    orchestrator.register_agent(planner, is_primary=True)
    
    # 启动编排器
    await orchestrator.start()
    
    # 创建任务
    task = TaskDefinition(
        task_id="task_001",
        name="固废碳排放分析",
        description="分析某城市的生活垃圾处理碳排放",
        input_data={"city": "示例城市", "total_waste": 1000}
    )
    
    # 执行任务
    result = await orchestrator.execute(task)
    print(f"任务结果: {result.output}")
    
    # 停止编排器
    await orchestrator.stop()

asyncio.run(main())
```

### 3. 使用领域工具

```python
from swagent.tools.domain.emission_calculator import EmissionCalculator

async def main():
    calculator = EmissionCalculator()
    
    result = await calculator.execute(
        waste_type="food_waste",
        treatment_method="composting",
        quantity=100,
        include_transport=True,
        transport_distance=50
    )
    
    if result.success:
        print(f"总排放量: {result.data['total_emission_kgCO2e']} kg CO2e")
    else:
        print(f"错误: {result.error}")

asyncio.run(main())
```

## 🔧 配置说明

### 配置文件 (config.yaml)

主配置文件位于项目根目录的 `config.yaml`，包含以下配置项：

- **LLM配置**: 模型选择、API密钥、超时等
- **Agent配置**: 默认参数、预定义Agent设置
- **工具配置**: 启用的工具、工具特定参数
- **领域配置**: 固废领域知识库路径、分类方法等
- **日志配置**: 日志级别、输出格式、文件位置
- **存储配置**: 数据存储方式（本地/Redis/MongoDB）

详细配置说明请参考 [INSTALLATION.md](INSTALLATION.md)。

### 环境变量

必需的环境变量：

- `OPENAI_API_KEY`: OpenAI API密钥（使用OpenAI模型时）

可选的环境变量：

- `SWAGENT_LOG_LEVEL`: 日志级别（DEBUG/INFO/WARNING/ERROR）
- `SWAGENT_DATA_PATH`: 数据存储路径

## 📖 核心概念

### Agent

Agent是框架的基本执行单元，每个Agent有特定的职责和专长：

- **PlannerAgent**: 任务规划，分解复杂任务
- **CoderAgent**: 代码生成与执行
- **WriterAgent**: 文档和报告撰写
- **ResearcherAgent**: 文献检索和研究
- **DataAgent**: 数据分析和处理
- **ReviewerAgent**: 内容审核和质量控制

### 消息系统

Agent之间通过消息进行通信，支持多种消息类型：

- REQUEST/RESPONSE: 请求-响应模式
- TASK/TASK_RESULT: 任务分配
- QUERY/INFORM: 查询和通知
- SYSTEM/ERROR: 系统消息和错误

### 编排器 (Orchestrator)

编排器负责协调多个Agent的协作，支持多种编排模式：

- **Sequential**: 顺序执行
- **Parallel**: 并行执行
- **Hierarchical**: 层级执行（有主Agent）
- **Collaborative**: 自由协作

### 工具系统

工具系统提供Agent可调用的功能：

- **内置工具**: 代码执行、文件处理、网络搜索等
- **领域工具**: 排放计算、LCA分析、废物分类等

## 🧪 测试

运行测试：

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_agents.py

# 运行示例
python examples/01_simple_chat.py
python examples/04_multi_agent.py
```

## 📊 开发路线图

- [x] Phase 1: 项目结构设计
- [ ] Phase 2: 核心框架实现
- [ ] Phase 3: Agent实现
- [ ] Phase 4: 工具系统完善
- [ ] Phase 5: 领域知识集成
- [ ] Phase 6: 工作流模板
- [ ] Phase 7: Web UI界面
- [ ] Phase 8: 文档和示例完善

详细路线图请参考 [.trae.md](.trae.md) 文档。

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 📮 联系方式

如有问题或建议，请通过以下方式联系：

- Issue: [GitHub Issues](https://github.com/yourusername/solidwaste-agent/issues)
- Email: your.email@example.com

## 🙏 致谢

本项目受以下框架启发：

- [LangChain](https://python.langchain.com/)
- [AutoGen](https://microsoft.github.io/autogen/)
- [MetaGPT](https://github.com/geekan/MetaGPT)

---

**注意**: 本项目目前处于开发阶段，API可能会发生变化。
