"""
GIS Agent 示例：天气查询和影像切片

演示如何使用天气查询工具和影像切片工具
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from swagent.tools.domain import WeatherTool, ImageryTool
from swagent.tools import ToolRegistry
from swagent.agents import ReActAgent
from swagent.llm import OpenAIClient, LLMConfig
from swagent.utils.logger import get_logger

logger = get_logger(__name__)


async def example_weather_tool():
    """示例 1: 直接使用天气工具"""
    print("\n" + "="*60)
    print("示例 1: 直接使用天气工具")
    print("="*60)

    weather_tool = WeatherTool()

    # 查询当前天气
    print("\n1. 查询北京当前天气:")
    result = await weather_tool.safe_execute(
        latitude=39.9042,
        longitude=116.4074
    )

    if result.success:
        print(f"✅ 成功!")
        print(f"模式: {result.data['mode']}")
        print(f"天气数据: {result.data['data']}")
    else:
        print(f"❌ 失败: {result.error}")

    # 查询指定时间的天气
    print("\n2. 查询北京指定时间天气:")
    result = await weather_tool.safe_execute(
        latitude=39.9042,
        longitude=116.4074,
        when="2026-01-20T14:00",
        timezone="Asia/Shanghai"
    )

    if result.success:
        print(f"✅ 成功!")
        print(f"模式: {result.data['mode']}")
        print(f"天气数据: {result.data['data']}")
    else:
        print(f"❌ 失败: {result.error}")


async def example_imagery_tool():
    """示例 2: 直接使用影像切片工具"""
    print("\n" + "="*60)
    print("示例 2: 直接使用影像切片工具")
    print("="*60)

    imagery_tool = ImageryTool()

    # 查询 Google Earth 影像（点位模式）- 保存到文件
    print("\n1. 查询 Google Earth 影像（点位）- 保存到文件:")
    result = await imagery_tool.safe_execute(
        location=[116.4074, 39.9042],
        source="google",
        zoom_level=18,
        point_size=1000,
        return_format="file",  # 保存到文件
        output_path="./imagery_output",  # 输出目录
        filename="beijing_google_earth.png"  # 自定义文件名
    )

    if result.success:
        print(f"✅ 成功!")
        print(f"数据源: {result.data['source']}")
        print(f"位置: {result.data['location']}")
        print(f"数组形状: {result.data['shape']}")
        print(f"模式: {result.data['mode']}")
        print(f"已保存到: {result.data['saved_path']}")
    else:
        print(f"❌ 失败: {result.error}")

    # 查询吉林一号影像（区域模式）- 自动生成文件名
    print("\n2. 查询吉林一号影像（区域）- 自动生成文件名:")
    result = await imagery_tool.safe_execute(
        location=[116.35, 39.85, 116.45, 39.95],
        source="jilin",
        zoom_level=17,
        year=2024,
        return_format="file",  # 保存到文件
        output_path="./imagery_output"  # 文件名将自动生成
    )

    if result.success:
        print(f"✅ 成功!")
        print(f"数据源: {result.data['source']}")
        print(f"位置: {result.data['location']}")
        print(f"数组形状: {result.data['shape']}")
        print(f"年份: {result.data['year']}")
        print(f"已保存到: {result.data['saved_path']}")
        print(f"文件名: {result.data['filename']}")
    else:
        print(f"❌ 失败: {result.error}")


async def example_with_registry():
    """示例 3: 使用工具注册中心"""
    print("\n" + "="*60)
    print("示例 3: 使用工具注册中心")
    print("="*60)

    # 创建工具注册中心
    registry = ToolRegistry()

    # 注册工具
    weather_tool = WeatherTool()
    imagery_tool = ImageryTool()

    registry.register(weather_tool)
    registry.register(imagery_tool)

    print("\n已注册的工具:")
    for tool_name in registry.list_tools():
        print(f"  - {tool_name}")

    # 通过注册中心执行工具
    print("\n使用注册中心查询天气:")
    result = await registry.execute_tool(
        "weather_query",
        latitude=39.9042,
        longitude=116.4074
    )

    if result.success:
        print(f"✅ 成功!")
        print(f"天气数据: {result.data['data']}")
    else:
        print(f"❌ 失败: {result.error}")


async def example_with_agent():
    """示例 4: 结合 Agent 使用（需要配置 LLM）"""
    print("\n" + "="*60)
    print("示例 4: 结合 ReAct Agent 使用")
    print("="*60)

    # 检查环境变量
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    if not api_key:
        print("⚠️ 跳过: 未配置 OPENAI_API_KEY 环境变量")
        print("提示: 设置环境变量后可以测试 Agent 功能:")
        print("  export OPENAI_API_KEY='your-api-key'")
        print("  export OPENAI_BASE_URL='your-base-url'  # 可选")
        return

    print("\n⚠️ 注意: Agent 集成示例需要完整的 Agent 框架支持")
    print("当前示例演示了工具的基本集成方式")
    print("完整的 Agent 功能请参考其他示例文件")

    # 演示如何准备工具给 Agent 使用
    print("\n准备工具供 Agent 使用:")
    registry = ToolRegistry()
    registry.register(WeatherTool())
    registry.register(ImageryTool())

    # 获取 OpenAI Function 格式的工具定义
    functions = registry.to_openai_functions()
    print(f"✓ 已准备 {len(functions)} 个工具")
    for func in functions:
        print(f"  - {func['function']['name']}: {func['function']['description'][:50]}...")

    print("\n提示: 在实际 Agent 中，这些工具会通过 Function Calling 被自动调用")


async def main():
    """主函数：运行所有示例"""
    print("\n" + "🚀"*30)
    print(" GIS Agent 工具演示")
    print("🚀"*30)

    # 示例 1: 直接使用天气工具
    await example_weather_tool()

    # 示例 2: 直接使用影像切片工具
    await example_imagery_tool()

    # 示例 3: 使用工具注册中心
    await example_with_registry()

    # 示例 4: 结合 Agent 使用
    await example_with_agent()

    print("\n" + "="*60)
    print("所有示例完成！")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
