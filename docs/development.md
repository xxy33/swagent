# SWAgent 开发指南

本指南帮助开发者了解如何为 SWAgent 项目做贡献，包括开发环境设置、代码规范、测试流程等。

## 目录

- [开发环境设置](#开发环境设置)
- [项目结构](#项目结构)
- [代码规范](#代码规范)
- [开发工作流](#开发工作流)
- [测试指南](#测试指南)
- [贡献指南](#贡献指南)
- [调试技巧](#调试技巧)

---

## 开发环境设置

### 前置要求

- Python 3.8 或更高版本
- Git
- pip 或 poetry（包管理器）
- （可选）virtualenv 或 conda

### 克隆仓库

```bash
git clone https://github.com/yourusername/swagent.git
cd swagent
```

### 创建虚拟环境

**使用 venv:**
```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

**使用 conda:**
```bash
conda create -n swagent python=3.8
conda activate swagent
```

### 安装依赖

**开发模式安装:**
```bash
# 安装核心依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt

# 或者使用 editable 模式安装项目本身
pip install -e .
```

**requirements-dev.txt** 内容:
```
# Testing
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0

# Code quality
black>=22.0.0
flake8>=5.0.0
mypy>=0.990
pylint>=2.15.0

# Documentation
sphinx>=5.0.0
sphinx-rtd-theme>=1.0.0

# Development tools
ipython>=8.0.0
jupyter>=1.0.0
```

### 配置环境变量

创建 `.env` 文件:
```bash
cp .env.example .env
```

编辑 `.env`:
```env
# OpenAI 配置
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# 模型配置
DEFAULT_MODEL=gpt-4
DEFAULT_TEMPERATURE=0.7

# 开发配置
DEBUG=true
LOG_LEVEL=INFO
```

### 验证安装

```bash
# 运行简单测试
python -c "import swagent; print(swagent.__version__)"

# 运行测试套件
pytest tests/

# 检查代码风格
black --check swagent/
flake8 swagent/
```

---

## 项目结构

```
swagent/
├── swagent/                    # 主包目录
│   ├── __init__.py
│   ├── llm/                   # LLM 接口层
│   │   ├── __init__.py
│   │   ├── base_llm.py
│   │   └── openai_client.py
│   │
│   ├── agent/                 # Agent 系统
│   │   ├── __init__.py
│   │   ├── base_agent.py
│   │   ├── planner_agent.py
│   │   ├── react_agent.py
│   │   ├── message_bus.py
│   │   └── orchestrator.py
│   │
│   ├── tools/                 # 工具系统
│   │   ├── __init__.py
│   │   ├── base_tool.py
│   │   ├── tool_registry.py
│   │   ├── builtin/           # 内置工具
│   │   │   ├── __init__.py
│   │   │   ├── code_executor.py
│   │   │   ├── file_handler.py
│   │   │   └── web_search.py
│   │   └── domain/            # 领域工具
│   │       ├── __init__.py
│   │       ├── emission_calculator.py
│   │       ├── lca_analyzer.py
│   │       └── visualizer.py
│   │
│   ├── domain/                # 领域增强
│   │   ├── __init__.py
│   │   ├── knowledge_base.py
│   │   ├── terminology.py
│   │   ├── standards.py
│   │   ├── prompts.py
│   │   └── data/              # 领域数据
│   │       ├── waste_categories.json
│   │       ├── treatment_methods.json
│   │       ├── terminology.json
│   │       └── standards.json
│   │
│   └── workflows/             # 工作流系统
│       ├── __init__.py
│       ├── base_workflow.py
│       ├── research_workflow.py
│       ├── report_workflow.py
│       ├── analysis_workflow.py
│       ├── coding_workflow.py
│       └── workflow_manager.py
│
├── tests/                     # 测试目录
│   ├── __init__.py
│   ├── test_phase1_llm.py
│   ├── test_phase2_agents.py
│   ├── test_phase3_multi_agent.py
│   ├── test_phase4_tools.py
│   ├── test_phase4_domain.py
│   └── test_phase5_workflows.py
│
├── examples/                  # 示例程序
│   ├── 01_basic_agent_demo.py
│   ├── 02_multi_agent_demo.py
│   ├── 03_tool_calling_demo.py
│   └── 04_domain_enhancement_demo.py
│
├── docs/                      # 文档
│   ├── user_guide.md
│   ├── api_reference.md
│   ├── architecture.md
│   └── development.md
│
├── .env.example               # 环境变量示例
├── .gitignore
├── requirements.txt           # 核心依赖
├── requirements-dev.txt       # 开发依赖
├── setup.py                   # 安装配置
├── README.md
├── LICENSE
└── CONTRIBUTING.md
```

### 模块职责

| 模块 | 职责 | 关键文件 |
|------|------|----------|
| `llm/` | LLM 接口和通信 | `base_llm.py`, `openai_client.py` |
| `agent/` | Agent 逻辑和协作 | `base_agent.py`, `orchestrator.py` |
| `tools/` | 工具定义和执行 | `base_tool.py`, `tool_registry.py` |
| `domain/` | 领域知识和增强 | `knowledge_base.py`, `terminology.py` |
| `workflows/` | 工作流模板 | `base_workflow.py`, `workflow_manager.py` |

---

## 代码规范

### Python 代码风格

SWAgent 遵循 **PEP 8** 和 **Google Python Style Guide**。

#### 格式化工具

使用 **Black** 自动格式化代码:
```bash
# 格式化整个项目
black swagent/

# 格式化特定文件
black swagent/agent/base_agent.py

# 检查而不修改
black --check swagent/
```

#### Linting

使用 **flake8** 检查代码质量:
```bash
# 检查整个项目
flake8 swagent/

# 检查特定文件
flake8 swagent/agent/base_agent.py
```

**flake8 配置** (.flake8):
```ini
[flake8]
max-line-length = 100
exclude = .git,__pycache__,build,dist,venv
ignore = E203,W503
```

#### 类型检查

使用 **mypy** 进行类型检查:
```bash
# 检查整个项目
mypy swagent/

# 检查特定文件
mypy swagent/agent/base_agent.py
```

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | PascalCase | `BaseAgent`, `OpenAIClient` |
| 函数/方法 | snake_case | `execute_task()`, `get_response()` |
| 变量 | snake_case | `agent_name`, `api_key` |
| 常量 | UPPER_SNAKE_CASE | `MAX_RETRIES`, `DEFAULT_TIMEOUT` |
| 私有成员 | _leading_underscore | `_internal_method()`, `_config` |
| 特殊方法 | __dunder__ | `__init__()`, `__repr__()` |

### 文档字符串

使用 **Google Style** docstrings:

```python
def execute_task(
    task: str,
    context: Optional[Dict[str, Any]] = None,
    timeout: int = 60
) -> str:
    """
    执行给定的任务。

    Args:
        task: 任务描述，应该是清晰的自然语言描述
        context: 任务执行的上下文信息，包含相关数据
        timeout: 执行超时时间（秒），默认 60 秒

    Returns:
        执行结果的字符串表示

    Raises:
        TaskExecutionError: 当任务执行失败时
        TimeoutError: 当执行超时时

    Example:
        >>> agent = ReActAgent("助手", llm=llm)
        >>> result = await agent.execute_task("分析废物处理方案")
        >>> print(result)
    """
    pass
```

### 导入顺序

按照以下顺序组织导入:

```python
# 1. 标准库
import os
import sys
from typing import Dict, List, Optional

# 2. 第三方库
import openai
from dotenv import load_dotenv

# 3. 本地模块
from swagent.llm import BaseLLM
from swagent.agent import BaseAgent
```

### 异步代码规范

```python
# ✓ 正确：使用 async/await
async def fetch_data(url: str) -> Dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# ✓ 正确：并发执行
results = await asyncio.gather(
    fetch_data(url1),
    fetch_data(url2)
)

# ✗ 错误：在 async 函数中使用同步调用
async def bad_example():
    result = requests.get(url)  # 阻塞事件循环！
    return result
```

### 错误处理

```python
# ✓ 正确：具体的异常类型
try:
    result = await tool.execute(**params)
except ToolNotFoundError as e:
    logger.error(f"Tool not found: {e}")
    raise
except ToolExecutionError as e:
    logger.error(f"Tool execution failed: {e}")
    # 处理或重新抛出
    raise

# ✓ 正确：使用自定义异常
class AgentExecutionError(Exception):
    """Agent 执行错误"""
    pass

# ✗ 错误：捕获所有异常
try:
    result = await agent.execute(task)
except Exception:  # 太宽泛
    pass
```

---

## 开发工作流

### 分支策略

采用 **Git Flow** 工作流:

```
main                 (生产分支)
  └── develop        (开发分支)
       ├── feature/xxx  (功能分支)
       ├── bugfix/xxx   (修复分支)
       └── hotfix/xxx   (热修复分支)
```

### 创建功能分支

```bash
# 1. 从 develop 创建功能分支
git checkout develop
git pull origin develop
git checkout -b feature/new-agent-type

# 2. 开发功能
# ... 编写代码 ...

# 3. 提交更改
git add .
git commit -m "feat: add new agent type

- Implement CustomAgent class
- Add tests for CustomAgent
- Update documentation"

# 4. 推送到远程
git push origin feature/new-agent-type

# 5. 创建 Pull Request
```

### Commit 规范

使用 **Conventional Commits** 格式:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 类型:**
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更改
- `style`: 代码格式（不影响功能）
- `refactor`: 重构（既不是新功能也不是修复）
- `test`: 添加或修改测试
- `chore`: 构建过程或辅助工具的变动

**示例:**
```bash
# 新功能
git commit -m "feat(agent): add debate mode for multi-agent collaboration"

# 修复 bug
git commit -m "fix(llm): handle rate limit errors properly

- Add exponential backoff
- Improve error messages"

# 文档
git commit -m "docs(readme): update installation instructions"

# 重构
git commit -m "refactor(tools): simplify tool registry implementation"
```

### Pull Request 流程

1. **创建 PR**: 在 GitHub 上创建 Pull Request
2. **填写描述**: 说明更改内容、动机和影响
3. **链接 Issue**: 如果相关，链接到对应的 Issue
4. **通过 CI**: 确保所有测试通过
5. **代码审查**: 等待维护者审查
6. **修改反馈**: 根据反馈修改代码
7. **合并**: 审查通过后合并到 develop

**PR 模板:**
```markdown
## 描述
简要描述这个 PR 做了什么

## 动机和上下文
为什么需要这个改动？它解决了什么问题？

## 改动类型
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## 测试
描述你进行的测试

## 检查清单
- [ ] 代码遵循项目的代码规范
- [ ] 进行了自我审查
- [ ] 添加了必要的注释
- [ ] 更新了相关文档
- [ ] 更改不会产生新的警告
- [ ] 添加了测试用例
- [ ] 所有测试通过
```

---

## 测试指南

### 测试框架

使用 **pytest** 和 **pytest-asyncio**:

```bash
# 安装
pip install pytest pytest-asyncio pytest-cov

# 运行所有测试
pytest tests/

# 运行特定文件
pytest tests/test_phase2_agents.py

# 运行特定测试
pytest tests/test_phase2_agents.py::test_base_agent

# 显示详细输出
pytest tests/ -v

# 生成覆盖率报告
pytest tests/ --cov=swagent --cov-report=html
```

### 测试结构

```python
# tests/test_phase2_agents.py
import pytest
from swagent.agent import BaseAgent, ReActAgent
from swagent.llm import OpenAIClient, LLMConfig

@pytest.fixture
def llm_config():
    """LLM 配置 fixture"""
    return LLMConfig(
        provider="openai",
        model="gpt-4",
        api_key="test_key",
        base_url="https://api.openai.com/v1"
    )

@pytest.fixture
def llm_client(llm_config):
    """LLM 客户端 fixture"""
    return OpenAIClient(llm_config)

@pytest.mark.asyncio
async def test_react_agent_execute(llm_client):
    """测试 ReAct Agent 执行"""
    # Arrange
    agent = ReActAgent("测试助手", llm=llm_client)
    task = "测试任务"

    # Act
    result = await agent.execute(task)

    # Assert
    assert isinstance(result, str)
    assert len(result) > 0

@pytest.mark.asyncio
async def test_react_agent_with_tools(llm_client):
    """测试 ReAct Agent 使用工具"""
    from swagent.tools import ToolRegistry
    from swagent.tools.builtin import CodeExecutor

    # Arrange
    registry = ToolRegistry()
    registry.register(CodeExecutor())

    agent = ReActAgent("测试助手", llm=llm_client)
    task = "执行代码: print('hello')"

    # Act
    result = await agent.execute(task)

    # Assert
    assert "hello" in result.lower()
```

### 测试最佳实践

#### 1. 使用 Fixtures

```python
@pytest.fixture
def sample_agent(llm_client):
    """创建示例 Agent"""
    return ReActAgent("测试", llm=llm_client)

def test_agent_name(sample_agent):
    assert sample_agent.name == "测试"
```

#### 2. 参数化测试

```python
@pytest.mark.parametrize("waste_type,expected", [
    ("food_waste", "composting"),
    ("plastic", "recycling"),
    ("mixed", "incineration")
])
def test_treatment_recommendation(waste_type, expected):
    kb = get_knowledge_base()
    treatments = kb.get_suitable_treatments(waste_type)
    assert expected in treatments
```

#### 3. 异步测试

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

#### 4. Mock 外部依赖

```python
from unittest.mock import Mock, AsyncMock, patch

@pytest.mark.asyncio
async def test_llm_call_with_mock():
    # Mock LLM 响应
    mock_llm = Mock()
    mock_llm.chat = AsyncMock(return_value=LLMResponse(
        content="Mock response",
        role="assistant"
    ))

    agent = ReActAgent("测试", llm=mock_llm)
    result = await agent.execute("测试任务")

    assert result == "Mock response"
    mock_llm.chat.assert_called_once()
```

#### 5. 测试异常处理

```python
@pytest.mark.asyncio
async def test_tool_not_found():
    registry = ToolRegistry()

    with pytest.raises(ToolNotFoundError):
        await registry.execute_tool("nonexistent_tool")
```

### 测试覆盖率

目标覆盖率: **≥ 80%**

```bash
# 生成覆盖率报告
pytest tests/ --cov=swagent --cov-report=html

# 查看报告
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

---

## 贡献指南

### 如何贡献

1. **Fork 项目**: 点击 GitHub 上的 Fork 按钮
2. **克隆 Fork**: `git clone https://github.com/YOUR_USERNAME/swagent.git`
3. **创建分支**: `git checkout -b feature/amazing-feature`
4. **提交更改**: `git commit -m "feat: add amazing feature"`
5. **推送分支**: `git push origin feature/amazing-feature`
6. **创建 PR**: 在 GitHub 上创建 Pull Request

### 贡献类型

#### 1. 报告 Bug

创建 Issue 时包含:
- Bug 描述
- 复现步骤
- 期望行为
- 实际行为
- 环境信息（Python 版本、OS 等）
- 相关日志或截图

#### 2. 提出新功能

创建 Issue 时包含:
- 功能描述
- 使用场景
- 预期效果
- 可能的实现方案

#### 3. 改进文档

- 修正错误
- 添加示例
- 改进说明
- 翻译文档

#### 4. 贡献代码

参考上述开发工作流和代码规范

### Code Review 指南

#### 作为作者

- **小而专注**: 每个 PR 只关注一个功能或修复
- **清晰描述**: 详细说明更改内容和原因
- **测试完善**: 确保添加了相应的测试
- **文档同步**: 更新相关文档
- **响应反馈**: 及时回应审查意见

#### 作为审查者

- **建设性反馈**: 提供具体、可操作的建议
- **关注重点**:
  - 代码正确性
  - 性能影响
  - 安全问题
  - 可维护性
  - 测试覆盖
- **及时审查**: 尽快完成审查
- **鼓励改进**: 认可好的实现

---

## 调试技巧

### 日志配置

```python
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('swagent.log'),
        logging.StreamHandler()
    ]
)

# 使用日志
logger = logging.getLogger(__name__)

logger.debug("调试信息")
logger.info("一般信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误")
```

### 调试 Agent 执行

```python
# 启用详细日志
import logging
logging.getLogger('swagent.agent').setLevel(logging.DEBUG)

# 使用 print 调试
class DebugAgent(ReActAgent):
    async def execute(self, task, context=None):
        print(f"[DEBUG] Executing task: {task}")
        print(f"[DEBUG] Context: {context}")

        result = await super().execute(task, context)

        print(f"[DEBUG] Result: {result}")
        return result

# 使用 IPython 进行交互式调试
from IPython import embed

async def debug_function():
    # ... some code ...
    embed()  # 进入交互式 shell
    # ... more code ...
```

### 调试异步代码

```python
import asyncio

# 启用 asyncio 调试模式
asyncio.run(main(), debug=True)

# 或设置环境变量
# PYTHONASYNCIODEBUG=1 python script.py

# 捕获未等待的协程
import warnings
warnings.simplefilter('always', ResourceWarning)
```

### 使用 Python Debugger (pdb)

```python
import pdb

async def debug_me():
    value = await some_function()
    pdb.set_trace()  # 设置断点
    result = process(value)
    return result

# 或使用 breakpoint() (Python 3.7+)
async def debug_me():
    value = await some_function()
    breakpoint()  # 设置断点
    result = process(value)
    return result
```

### 性能分析

```python
# 使用 cProfile
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# 执行代码
await agent.execute(task)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(10)  # 显示前 10 个最耗时的函数

# 使用 line_profiler
# pip install line_profiler
# kernprof -l -v script.py

@profile
def expensive_function():
    # 逐行分析
    pass
```

### 内存分析

```python
# 使用 memory_profiler
# pip install memory_profiler
from memory_profiler import profile

@profile
def memory_intensive_function():
    data = [i for i in range(1000000)]
    return data

# 使用 tracemalloc
import tracemalloc

tracemalloc.start()

# 执行代码
result = await agent.execute(task)

# 获取内存快照
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

for stat in top_stats[:10]:
    print(stat)
```

---

## 常见开发问题

### 1. API 速率限制

**问题**: OpenAI API 返回 429 错误

**解决方案**:
```python
from swagent.llm import RateLimiter

# 使用速率限制器
limiter = RateLimiter(rate=60, per=60.0)  # 60 请求/分钟

async def call_api():
    await limiter.acquire()
    response = await llm.chat(messages)
    return response
```

### 2. 异步代码阻塞

**问题**: 事件循环被阻塞

**解决方案**:
```python
# ✗ 错误：同步 I/O 阻塞事件循环
async def bad():
    data = open('file.txt').read()  # 阻塞！

# ✓ 正确：使用异步 I/O
async def good():
    async with aiofiles.open('file.txt') as f:
        data = await f.read()

# ✓ 或在线程池中运行同步代码
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def also_good():
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as pool:
        data = await loop.run_in_executor(
            pool,
            lambda: open('file.txt').read()
        )
```

### 3. 测试环境配置

**问题**: 测试时不想调用真实 API

**解决方案**:
```python
# 使用环境变量切换
import os

if os.getenv('TESTING') == 'true':
    # 使用 mock
    llm = MockLLMClient()
else:
    # 使用真实客户端
    llm = OpenAIClient(config)

# 或使用 pytest fixtures
@pytest.fixture
def mock_llm():
    return MockLLMClient()
```

### 4. 导入错误

**问题**: ModuleNotFoundError

**解决方案**:
```bash
# 确保项目根目录在 PYTHONPATH 中
export PYTHONPATH="${PYTHONPATH}:/path/to/swagent"

# 或使用 editable 安装
pip install -e .

# 在代码中添加路径（不推荐）
import sys
sys.path.insert(0, '/path/to/swagent')
```

---

## CI/CD 配置

### GitHub Actions 示例

创建 `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10]

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v2
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Lint with flake8
      run: |
        flake8 swagent/ --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 swagent/ --count --exit-zero --max-complexity=10 --max-line-length=100 --statistics

    - name: Check code formatting
      run: |
        black --check swagent/

    - name: Type check with mypy
      run: |
        mypy swagent/

    - name: Test with pytest
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      run: |
        pytest tests/ --cov=swagent --cov-report=xml

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v2
      with:
        file: ./coverage.xml
```

---

## 发布流程

### 版本号规范

遵循 **Semantic Versioning** (semver):

```
MAJOR.MINOR.PATCH

- MAJOR: 不兼容的 API 更改
- MINOR: 向后兼容的新功能
- PATCH: 向后兼容的 bug 修复
```

### 发布步骤

```bash
# 1. 更新版本号
# 编辑 swagent/__init__.py
__version__ = "1.1.0"

# 2. 更新 CHANGELOG.md
# 记录所有重要更改

# 3. 提交更改
git add .
git commit -m "chore: bump version to 1.1.0"

# 4. 创建标签
git tag -a v1.1.0 -m "Release version 1.1.0"

# 5. 推送到远程
git push origin develop
git push origin v1.1.0

# 6. 创建 Release
# 在 GitHub 上创建 Release，附上 CHANGELOG

# 7. （可选）发布到 PyPI
python setup.py sdist bdist_wheel
twine upload dist/*
```

---

## 资源链接

### 官方文档
- [Python 官方文档](https://docs.python.org/3/)
- [asyncio 文档](https://docs.python.org/3/library/asyncio.html)
- [pytest 文档](https://docs.pytest.org/)

### 代码规范
- [PEP 8](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Conventional Commits](https://www.conventionalcommits.org/)

### 工具
- [Black](https://github.com/psf/black) - 代码格式化
- [flake8](https://flake8.pycqa.org/) - 代码检查
- [mypy](https://mypy.readthedocs.io/) - 类型检查
- [pytest](https://docs.pytest.org/) - 测试框架

---

## 获取帮助

- **文档**: 查看 [用户指南](user_guide.md) 和 [API 参考](api_reference.md)
- **Issues**: 在 GitHub 上创建 Issue
- **讨论**: 参与 GitHub Discussions
- **联系**: 发送邮件到 swagent@example.com

---

## 许可证

本项目采用 MIT 许可证。贡献代码即表示您同意在相同许可证下发布您的贡献。

---

**感谢您对 SWAgent 的贡献！** 🎉
