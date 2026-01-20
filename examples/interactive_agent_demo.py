"""
交互式 GIS Agent 演示
模拟用户交互，展示核心功能
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from swagent.tools import ToolRegistry
from swagent.tools.domain import WeatherTool, ImageryTool


async def demo_weather_query():
    """演示天气查询"""
    print("\n" + "="*60)
    print("🌤️  演示 1: 天气查询")
    print("="*60)

    registry = ToolRegistry()
    registry.register(WeatherTool())

    cities = {
        "北京": (116.4074, 39.9042),
        "上海": (121.4737, 31.2304),
        "广州": (113.2644, 23.1291),
    }

    for city, (lon, lat) in cities.items():
        print(f"\n👤 用户: 查询{city}的天气")
        print(f"\n🌤️  正在查询 {city} 的天气...")

        result = await registry.execute_tool(
            "weather_query",
            latitude=lat,
            longitude=lon
        )

        if result.success:
            data = result.data['data']
            print(f"\n🤖 Agent:")
            print(f"📍 {city} 当前天气:")
            print(f"   🌡️  温度: {data.get('temperature_2m')}°C")
            print(f"   💧 湿度: {data.get('relative_humidity_2m')}%")
            print(f"   🌧️  降水: {data.get('precipitation')} mm")
            print(f"   💨 风速: {data.get('wind_speed_10m')} km/h")

        await asyncio.sleep(1)  # 模拟思考时间


async def demo_imagery_query():
    """演示影像查询"""
    print("\n" + "="*60)
    print("🛰️  演示 2: 卫星影像获取")
    print("="*60)

    registry = ToolRegistry()
    registry.register(ImageryTool())

    city = "深圳"
    coords = (114.0579, 22.5431)

    print(f"\n👤 用户: 下载{city}的卫星影像")
    print(f"\n🛰️  正在获取 {city} 的卫星影像...")

    result = await registry.execute_tool(
        "imagery_query",
        location=[coords[0], coords[1]],
        source="google",
        zoom_level=18,
        point_size=1000,
        return_format="file",
        output_path="./demo_images",
        filename=f"{city}_satellite.png"
    )

    if result.success:
        data = result.data
        print(f"\n🤖 Agent:")
        print(f"📍 {city} 卫星影像:")
        print(f"   🗺️  数据源: {data.get('source')}")
        print(f"   📐 影像尺寸: {data.get('shape')[0]}x{data.get('shape')[1]} 像素")
        if 'saved_path' in data:
            print(f"   💾 已保存到: {data.get('saved_path')}")
            print(f"   📄 文件名: {data.get('filename')}")
    else:
        print(f"\n🤖 Agent: 抱歉，获取影像失败: {result.error}")


async def demo_interactive_commands():
    """演示交互命令"""
    print("\n" + "="*60)
    print("💬 演示 3: 交互式命令")
    print("="*60)

    commands = [
        ("help", "显示帮助信息"),
        ("clear", "清空对话历史"),
        ("quit", "退出程序")
    ]

    for cmd, desc in commands:
        print(f"\n👤 用户: {cmd}")
        print(f"🤖 Agent: {desc}")
        await asyncio.sleep(0.5)


async def demo_error_handling():
    """演示错误处理"""
    print("\n" + "="*60)
    print("⚠️  演示 4: 错误处理")
    print("="*60)

    registry = ToolRegistry()
    registry.register(WeatherTool())

    print("\n👤 用户: 查询火星的天气")
    print("\n🤖 Agent: 抱歉，我只能查询地球上城市的天气。")
    print("   支持的城市：北京、上海、广州、深圳、成都、杭州")


async def main():
    """运行所有演示"""
    print("\n" + "🌍"*30)
    print(" 交互式 GIS Agent - 功能演示")
    print("🌍"*30)

    print("\n提示: 这是一个自动化演示，展示 Agent 的核心功能")
    print("      实际使用时，您可以与 Agent 进行实时对话\n")

    await asyncio.sleep(2)

    # 运行演示
    await demo_weather_query()
    await asyncio.sleep(1)

    await demo_imagery_query()
    await asyncio.sleep(1)

    await demo_interactive_commands()
    await asyncio.sleep(1)

    await demo_error_handling()

    print("\n" + "="*60)
    print("✅ 演示完成！")
    print("="*60)

    print("\n开始使用:")
    print("  方式 1: ./start_gis_agent.sh")
    print("  方式 2: python examples/interactive_gis_agent.py")
    print()


if __name__ == "__main__":
    asyncio.run(main())
