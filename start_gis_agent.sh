#!/bin/bash

# 交互式 GIS Agent 启动脚本（LLM 驱动）

echo "=================================="
echo "🌍 启动交互式 GIS Agent (LLM驱动)"
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

# 检查环境变量（必需）
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ 错误: 未配置 OPENAI_API_KEY"
    echo
    echo "本 Agent 使用 LLM Function Calling 进行智能分析"
    echo "必须配置 OpenAI API Key 才能运行"
    echo
    echo "配置方式:"
    echo "  export OPENAI_API_KEY='your-api-key'"
    echo "  export OPENAI_BASE_URL='your-base-url'  # 可选"
    echo
    echo "然后重新运行此脚本"
    exit 1
else
    echo "✅ 检测到 OPENAI_API_KEY"
    echo "✅ 将使用 LLM Function Calling 模式"
    echo
fi

# 运行脚本
echo "正在启动..."
echo
python examples/interactive_gis_agent.py

