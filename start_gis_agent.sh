#!/bin/bash

# 交互式 GIS Agent 启动脚本

echo "=================================="
echo "🌍 启动交互式 GIS Agent"
echo "=================================="
echo

# 检查 Python
if ! command -v python &> /dev/null; then
    echo "❌ 错误: 未找到 Python"
    exit 1
fi

# 检查依赖
echo "检查依赖..."
python -c "import requests, PIL, numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  警告: 部分依赖缺失"
    echo "   运行: pip install requests Pillow numpy"
fi

# 检查环境变量
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  提示: 未配置 OPENAI_API_KEY"
    echo "   将使用简化模式（关键词匹配）"
    echo "   配置后可启用智能对话模式"
    echo
    echo "   export OPENAI_API_KEY='your-api-key'"
    echo "   export OPENAI_BASE_URL='your-base-url'  # 可选"
    echo
else
    echo "✅ 检测到 OPENAI_API_KEY，将使用智能模式"
    echo
fi

# 运行脚本
echo "正在启动..."
echo
python examples/interactive_gis_agent.py
