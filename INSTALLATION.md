# 安装与配置指南

本文档提供 SolidWaste-Agent 框架的详细安装和配置说明。

## 📋 目录

- [系统要求](#系统要求)
- [安装步骤](#安装步骤)
- [配置说明](#配置说明)
- [验证安装](#验证安装)
- [常见问题](#常见问题)
- [高级配置](#高级配置)

## 系统要求

### 硬件要求

- **最小配置**:
  - CPU: 双核处理器
  - 内存: 4GB RAM
  - 硬盘: 1GB 可用空间

- **推荐配置**:
  - CPU: 四核或更高处理器
  - 内存: 8GB+ RAM
  - 硬盘: 5GB+ 可用空间（用于模型缓存和数据）

### 软件要求

- **操作系统**:
  - Windows 10/11
  - macOS 10.15+
  - Linux (Ubuntu 18.04+, CentOS 7+)

- **Python**: 3.8, 3.9, 3.10, 3.11（推荐 3.10）

- **其他工具**:
  - pip (Python 包管理器)
  - Git (可选，用于克隆仓库)

## 安装步骤

### 1. 安装 Python

#### Windows

1. 访问 [Python官网](https://www.python.org/downloads/)
2. 下载 Python 3.10+ 安装程序
3. 运行安装程序，**勾选 "Add Python to PATH"**
4. 验证安装：
   ```bash
   python --version
   pip --version
   ```

#### macOS

使用 Homebrew 安装：
```bash
brew install python@3.10
```

或从官网下载安装包。

#### Linux

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.10 python3-pip python3-venv

# CentOS/RHEL
sudo yum install python3 python3-pip
```

### 2. 获取项目代码

如果你已经在项目目录中，可以跳过此步骤。

**选项A: 使用Git克隆（推荐）**
```bash
git clone https://github.com/yourusername/solidwaste-agent.git
cd solidwaste-agent
```

**选项B: 下载ZIP文件**
1. 下载项目ZIP文件
2. 解压到目标目录
3. 进入项目目录

### 3. 创建虚拟环境

**强烈推荐使用虚拟环境**，以避免包冲突。

#### Windows
```bash
# 进入项目目录
cd c:\Users\CHENXY\Desktop\x\vscode\envagent

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 激活后，命令提示符会显示 (venv) 前缀
```

#### Linux/macOS
```bash
# 进入项目目录
cd /path/to/envagent

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 激活后，命令提示符会显示 (venv) 前缀
```

### 4. 安装依赖包

确保虚拟环境已激活（命令提示符显示 `(venv)`），然后运行：

```bash
# 升级 pip
python -m pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

如果你想以开发模式安装（可编辑安装）：

```bash
pip install -e .
```

### 5. 配置环境变量

#### 方法A: 使用 .env 文件（推荐）

1. 复制示例文件：
   ```bash
   # Windows
   copy .env.example .env
   
   # Linux/macOS
   cp .env.example .env
   ```

2. 编辑 `.env` 文件，添加你的配置：
   ```bash
   # OpenAI API配置
   OPENAI_API_KEY=sk-your-api-key-here
   OPENAI_BASE_URL=https://api.openai.com/v1
   
   # 日志配置
   SWAGENT_LOG_LEVEL=INFO
   
   # 数据路径
   SWAGENT_DATA_PATH=./data
   ```

#### 方法B: 系统环境变量

**Windows (CMD)**
```bash
set OPENAI_API_KEY=sk-your-api-key-here
set SWAGENT_LOG_LEVEL=INFO
```

**Windows (PowerShell)**
```powershell
$env:OPENAI_API_KEY="sk-your-api-key-here"
$env:SWAGENT_LOG_LEVEL="INFO"
```

**Linux/macOS**
```bash
export OPENAI_API_KEY=sk-your-api-key-here
export SWAGENT_LOG_LEVEL=INFO

# 永久设置（添加到 ~/.bashrc 或 ~/.zshrc）
echo 'export OPENAI_API_KEY=sk-your-api-key-here' >> ~/.bashrc
source ~/.bashrc
```

### 6. 配置 config.yaml

编辑项目根目录下的 `config.yaml` 文件：

```yaml
# 应用信息
app:
  name: "SolidWaste-Agent"
  version: "0.1.0"

# LLM配置
llm:
  default_provider: "openai"  # 或 "local"
  providers:
    openai:
      api_key: "${OPENAI_API_KEY}"  # 从环境变量读取
      default_model: "gpt-4"
      timeout: 60

# Agent配置
agents:
  default_temperature: 0.7
  default_max_tokens: 4096

# 日志配置
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  file: "./logs/swagent.log"
```

## 验证安装

### 1. 检查Python环境

```bash
python --version
# 应输出: Python 3.8.x 或更高版本

pip list
# 应显示已安装的包列表
```

### 2. 测试导入

```bash
python -c "import swagent; print('SWAgent installed successfully!')"
```

### 3. 运行简单示例

```bash
python examples/01_simple_chat.py
```

如果一切正常，你应该看到Agent的响应输出。

### 4. 运行测试套件

```bash
# 安装pytest（如果还没安装）
pip install pytest

# 运行测试
pytest tests/ -v
```

## 常见问题

### Q1: 找不到 Python 命令

**问题**: 运行 `python` 时提示 "命令未找到"

**解决方案**:
- Windows: 重新安装Python并勾选 "Add Python to PATH"
- Linux/macOS: 尝试使用 `python3` 而非 `python`
- 检查环境变量PATH是否包含Python安装目录

### Q2: pip 安装依赖失败

**问题**: `pip install -r requirements.txt` 报错

**解决方案**:
```bash
# 升级pip
python -m pip install --upgrade pip

# 使用国内镜像（如果网络慢）
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 如果某个包安装失败，尝试单独安装
pip install package-name --upgrade
```

### Q3: OpenAI API 连接失败

**问题**: 提示 "OpenAI API connection error"

**解决方案**:
- 确认API密钥正确设置
- 检查网络连接
- 验证API密钥是否有效
- 如果在中国大陆，可能需要使用代理或中转API

```python
# 测试API连接
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")
try:
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello"}]
    )
    print("API连接成功!")
except Exception as e:
    print(f"API连接失败: {e}")
```

### Q4: 虚拟环境激活失败

**问题**: Windows上激活虚拟环境时提示"无法加载文件"

**解决方案**:
```powershell
# PowerShell执行策略问题
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 然后重新激活
venv\Scripts\activate
```

### Q5: 导入swagent模块失败

**问题**: `ModuleNotFoundError: No module named 'swagent'`

**解决方案**:
```bash
# 确保在项目根目录
cd c:\Users\CHENXY\Desktop\x\vscode\envagent

# 以开发模式安装
pip install -e .

# 或将项目路径添加到PYTHONPATH
# Windows (CMD)
set PYTHONPATH=%cd%;%PYTHONPATH%

# Linux/macOS
export PYTHONPATH=$(pwd):$PYTHONPATH
```

## 高级配置

### 使用本地LLM模型

如果你想使用本地模型而非OpenAI API：

1. 安装本地LLM服务（如Ollama, llama.cpp等）

2. 修改 `config.yaml`:
```yaml
llm:
  default_provider: "local"
  providers:
    local:
      base_url: "http://localhost:8000"
      default_model: "qwen-7b"
      timeout: 120
```

3. 确保本地模型服务正在运行

### 配置数据存储

#### 使用 Redis

```yaml
storage:
  type: "redis"
  redis:
    host: "localhost"
    port: 6379
    db: 0
    password: ""  # 如果有密码
```

安装Redis客户端：
```bash
pip install redis
```

#### 使用 MongoDB

```yaml
storage:
  type: "mongodb"
  mongodb:
    host: "localhost"
    port: 27017
    database: "swagent"
    username: ""
    password: ""
```

安装MongoDB客户端：
```bash
pip install pymongo
```

### 日志配置

#### 高级日志设置

编辑 `config.yaml`:

```yaml
logging:
  level: "DEBUG"  # 开发时使用DEBUG级别
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "./logs/swagent.log"
  max_size: "10MB"
  backup_count: 5
  console: true  # 是否同时输出到控制台
```

#### 查看日志

```bash
# Windows
type logs\swagent.log

# Linux/macOS
tail -f logs/swagent.log
```

### 性能优化

#### 并发配置

```yaml
orchestrator:
  max_concurrent_agents: 5
  task_timeout: 300  # 秒
  retry_on_failure: true
  max_retries: 3
```

#### 缓存配置

```yaml
cache:
  enabled: true
  backend: "memory"  # memory, redis, disk
  ttl: 3600  # 缓存过期时间（秒）
```

## 下一步

安装完成后，你可以：

1. 📖 阅读 [README.md](README.md) 了解项目概述
2. 💡 查看 [examples/](examples/) 目录学习使用方法
3. 🏗️ 阅读 [docs/architecture.md](docs/architecture.md) 了解架构设计
4. 🛠️ 参考 [docs/development_guide.md](docs/development_guide.md) 开始开发

## 获取帮助

如果遇到问题：

1. 检查本文档的[常见问题](#常见问题)部分
2. 查看项目 [GitHub Issues](https://github.com/yourusername/solidwaste-agent/issues)
3. 提交新的Issue描述你的问题

---

**祝你使用愉快！** 🎉
