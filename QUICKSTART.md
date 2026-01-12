# 🚀 快速启动指南

本指南帮助你在5分钟内启动 SolidWaste-Agent 项目。

## ⚡ 快速开始（3步）

### 1️⃣ 创建虚拟环境并安装依赖

```bash
# Windows
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2️⃣ 配置API密钥

```bash
# 复制环境变量示例文件
copy .env.example .env  # Windows
# 或
cp .env.example .env    # Linux/macOS

# 编辑 .env 文件，添加你的OpenAI API密钥
# OPENAI_API_KEY=sk-your-key-here
```

### 3️⃣ 运行示例

```bash
python examples/00_quick_start.py
```

## 📂 项目结构

```
envagent/
├── 📄 README.md              # 项目说明
├── 📄 INSTALLATION.md        # 详细安装指南
├── 📄 QUICKSTART.md          # 快速启动（本文件）
├── 📄 requirements.txt       # 依赖包
├── 📄 config.yaml            # 配置文件
├── 📄 .env.example           # 环境变量示例
│
├── 📂 swagent/               # 核心包
│   ├── core/                 # 核心模块
│   ├── agents/               # Agent实现
│   ├── tools/                # 工具系统
│   ├── domain/               # 固废领域知识
│   ├── llm/                  # LLM接口
│   └── utils/                # 工具函数
│
├── 📂 workflows/             # 工作流
├── 📂 examples/              # 示例代码
├── 📂 tests/                 # 测试
├── 📂 docs/                  # 文档
├── 📂 data/                  # 数据目录
└── 📂 logs/                  # 日志目录
```

## 🎯 核心概念

### Agent（智能体）
- **PlannerAgent**: 任务规划
- **CoderAgent**: 代码生成
- **WriterAgent**: 文档撰写
- **ResearcherAgent**: 研究辅助
- **DataAgent**: 数据分析
- **ReviewerAgent**: 质量审核

### 编排模式
- **Sequential**: 顺序执行
- **Parallel**: 并行执行
- **Hierarchical**: 层级执行
- **Collaborative**: 协作执行

### 领域工具
- 排放计算器
- LCA分析器
- 废物分类器
- 政策合规检查器

## 📝 配置说明

### config.yaml 主要配置

```yaml
# LLM配置
llm:
  default_provider: "openai"
  providers:
    openai:
      default_model: "gpt-4"

# Agent配置
agents:
  default_temperature: 0.7
  default_max_tokens: 4096

# 日志配置
logging:
  level: "INFO"
  file: "./logs/swagent.log"
```

### 环境变量

必需：
- `OPENAI_API_KEY`: OpenAI API密钥

可选：
- `SWAGENT_LOG_LEVEL`: 日志级别（INFO/DEBUG/WARNING）
- `SWAGENT_DATA_PATH`: 数据存储路径

## 🔨 开发任务清单

项目框架已搭建完成，接下来需要实现：

- [ ] **核心模块** (swagent/core/)
  - [ ] base_agent.py - Agent基类
  - [ ] message.py - 消息系统
  - [ ] context.py - 上下文管理
  - [ ] communication.py - 通信协议
  - [ ] orchestrator.py - 编排调度器
  - [ ] memory.py - 记忆系统

- [ ] **Agent实现** (swagent/agents/)
  - [ ] planner_agent.py - 规划Agent
  - [ ] coder_agent.py - 代码Agent
  - [ ] writer_agent.py - 写作Agent
  - [ ] researcher_agent.py - 研究Agent
  - [ ] data_agent.py - 数据Agent
  - [ ] reviewer_agent.py - 审核Agent

- [ ] **工具系统** (swagent/tools/)
  - [ ] base_tool.py - 工具基类
  - [ ] tool_registry.py - 工具注册
  - [ ] builtin/ - 内置工具
  - [ ] domain/ - 领域工具（排放计算器等）

- [ ] **LLM接口** (swagent/llm/)
  - [ ] base_llm.py - LLM基类
  - [ ] openai_client.py - OpenAI客户端
  - [ ] prompt_manager.py - Prompt管理

- [ ] **工作流** (workflows/)
  - [ ] research_workflow.py - 科研工作流
  - [ ] report_workflow.py - 报告工作流
  - [ ] analysis_workflow.py - 分析工作流

- [ ] **示例代码** (examples/)
  - [ ] 01_simple_chat.py
  - [ ] 02_code_generation.py
  - [ ] 03_report_writing.py
  - [ ] 04_multi_agent.py
  - [ ] 05_domain_analysis.py

## 📚 参考资料

### 项目文档
- [README.md](README.md) - 项目概述
- [INSTALLATION.md](INSTALLATION.md) - 详细安装指南
- [.trae.md](.trae.md) - 完整架构设计文档

### 外部资源
- [LangChain文档](https://python.langchain.com/)
- [AutoGen文档](https://microsoft.github.io/autogen/)
- [OpenAI API文档](https://platform.openai.com/docs)

## 🐛 常见问题

**Q: 如何切换到本地模型？**
```yaml
# 修改 config.yaml
llm:
  default_provider: "local"
  providers:
    local:
      base_url: "http://localhost:8000"
      default_model: "qwen-7b"
```

**Q: 如何启用调试日志？**
```bash
# 设置环境变量
set SWAGENT_LOG_LEVEL=DEBUG  # Windows
export SWAGENT_LOG_LEVEL=DEBUG  # Linux/macOS
```

**Q: 安装依赖失败？**
```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 💡 使用提示

1. **开发模式安装**：使用 `pip install -e .` 可以在开发时实时生效代码修改
2. **日志查看**：日志文件位于 `logs/swagent.log`
3. **数据存储**：所有数据存储在 `data/` 目录下
4. **配置优先级**：环境变量 > config.yaml > 默认值

## 🎉 下一步

1. 阅读 [.trae.md](.trae.md) 了解完整的架构设计
2. 开始实现核心模块
3. 编写测试用例
4. 运行示例代码验证功能

---

**祝开发顺利！** 如有问题，请查看文档或提交Issue。
