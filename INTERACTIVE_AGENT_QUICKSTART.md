# 交互式 GIS Agent - 快速开始

## 🚀 快速启动

### 方式 1: 使用启动脚本（推荐）

```bash
./start_gis_agent.sh
```

### 方式 2: 直接运行

```bash
python examples/interactive_gis_agent.py
```

## 📋 功能概览

这是一个**命令行交互式 Agent**，可以：

✅ 在终端与用户对话
✅ 自动调用天气查询工具
✅ 自动调用卫星影像工具
✅ 支持自然语言（智能模式）或关键词匹配（简化模式）

## 💬 使用示例

### 启动后的交互

```
🌍 交互式 GIS Agent
====================================

功能:
  1. 🌤️  天气查询 - 查询城市的实时天气
  2. 🛰️  卫星影像 - 获取/下载卫星图片

支持的城市:
  北京、上海、广州、深圳、成都、杭州

开始对话... (输入 'help' 查看帮助, 'quit' 退出)

👤 您: 查询北京的天气

🌤️  正在查询 北京 的天气...

🤖 Agent:
📍 北京 当前天气:
   🌡️  温度: -7.5°C
   💧 湿度: 18%
   🌧️  降水: 0.0 mm
   💨 风速: 12.5 km/h
   ⏰ 时间: 2026-01-20T11:15

👤 您: 下载上海的卫星影像

🛰️  正在获取 上海 的卫星影像...

🤖 Agent:
📍 上海 卫星影像:
   🗺️  数据源: google
   📐 影像尺寸: 1000x1000 像素
   💾 已保存到: /root/swagent/satellite_images/上海_satellite.png
   📄 文件名: 上海_satellite.png

👤 您: quit

👋 再见！
```

## 🎯 两种模式

### 智能模式（需要 LLM）

**配置**：
```bash
export OPENAI_API_KEY='your-api-key'
export OPENAI_BASE_URL='your-base-url'  # 可选

./start_gis_agent.sh
```

**特点**：
- ✅ 理解自然语言
- ✅ 自动选择工具
- ✅ Function Calling
- ✅ 上下文对话

### 简化模式（无需配置）

**直接运行**：
```bash
./start_gis_agent.sh
```

**特点**：
- ✅ 关键词匹配
- ✅ 快速响应
- ✅ 无需 API
- ⚠️ 功能有限

## 📝 命令和示例

### 天气查询

```
查询北京的天气
广州现在温度多少
深圳天气怎么样
```

### 影像下载

```
下载上海的卫星影像
获取杭州的卫星图片
保存成都的影像
```

### 系统命令

- `help` - 显示帮助
- `quit` - 退出
- `clear` - 清空历史（智能模式）

## 📂 输出文件

影像文件默认保存到：
```
./satellite_images/
├── 北京_satellite.png
├── 上海_satellite.png
└── ...
```

## 🔧 依赖要求

### 必需
```bash
pip install requests
```

### 影像功能（可选）
```bash
pip install Pillow numpy mercantile
```

### 智能模式（可选）
```bash
export OPENAI_API_KEY='your-key'
```

## 📖 详细文档

- **使用指南**: [docs/INTERACTIVE_GIS_AGENT.md](docs/INTERACTIVE_GIS_AGENT.md)
- **GIS 工具**: [docs/GIS_TOOLS.md](docs/GIS_TOOLS.md)

## 🛠️ 故障排除

### 问题：无法连接 API

**简化模式**仍可用（关键词匹配）

### 问题：影像下载失败

```bash
# 安装依赖
pip install mercantile
```

### 问题：城市不识别

当前支持：**北京、上海、广州、深圳、成都、杭州**

## 🎨 扩展

添加更多城市，编辑 `examples/interactive_gis_agent.py`：

```python
cities = {
    "北京": (116.4074, 39.9042),
    "你的城市": (经度, 纬度),
}
```

## 🌟 开始体验

```bash
./start_gis_agent.sh
```

或

```bash
python examples/interactive_gis_agent.py
```

享受与 GIS Agent 的交互！🌍
