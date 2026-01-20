"""
交互式 GIS Agent
在终端中与用户交互，自动调用天气查询和影像切片工具
"""
import asyncio
import os
import sys
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from swagent.tools import ToolRegistry
from swagent.tools.domain import WeatherTool, ImageryTool
from swagent.llm import OpenAIClient, LLMConfig
from swagent.utils.logger import get_logger

logger = get_logger(__name__)


class InteractiveGISAgent:
    """交互式 GIS Agent"""

    def __init__(self):
        self.registry = ToolRegistry()
        self.llm = None
        self.conversation_history = []

    def initialize_llm(self):
        """初始化 LLM"""
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = os.getenv("DEFAULT_MODEL", "gpt-4")

        if not api_key:
            print("❌ 错误: 未配置 OPENAI_API_KEY 环境变量")
            print("请设置环境变量:")
            print("  export OPENAI_API_KEY='your-api-key'")
            print("  export OPENAI_BASE_URL='your-base-url'  # 可选")
            return False

        try:
            config = LLMConfig(
                provider="openai",
                model=model,
                api_key=api_key,
                base_url=base_url,
                temperature=0.7
            )
            self.llm = OpenAIClient(config)
            logger.info(f"LLM 初始化成功 - 模型: {model}")
            return True
        except Exception as e:
            print(f"❌ LLM 初始化失败: {e}")
            return False

    def initialize_tools(self):
        """初始化工具"""
        try:
            # 注册工具
            self.registry.register(WeatherTool())
            self.registry.register(ImageryTool())

            logger.info("工具注册成功")
            return True
        except Exception as e:
            print(f"❌ 工具初始化失败: {e}")
            return False

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的 GIS (地理信息系统) 助手，可以帮助用户查询天气和获取卫星影像。

你有以下工具可用：
1. weather_query - 根据坐标查询天气数据（温度、湿度、降水、风速）
2. imagery_query - 获取卫星影像（Google Earth、吉林一号、Sentinel-2）

用户可能会：
- 询问某个地点的天气
- 请求下载卫星影像
- 询问如何使用这些功能

重要提示：
- 当用户提到城市名称时，你需要知道常见城市的大致坐标
- 对于天气查询，默认使用当前时间
- 对于影像查询，默认使用 Google Earth 数据源，zoom_level=18
- 如果用户要保存影像，使用 return_format="file"

常见城市坐标参考：
- 北京: (116.4074, 39.9042)
- 上海: (121.4737, 31.2304)
- 广州: (113.2644, 23.1291)
- 深圳: (114.0579, 22.5431)
- 成都: (104.0668, 30.5728)
- 杭州: (120.1551, 30.2741)

请用中文回复，简洁明了。当你需要调用工具时，请清晰说明你在做什么。"""

    async def call_llm_with_tools(self, user_message: str) -> str:
        """调用 LLM 并处理工具调用"""
        # 添加用户消息到历史
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # 准备消息
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
            *self.conversation_history
        ]

        # 获取可用工具的 OpenAI Function 格式
        functions = self.registry.to_openai_functions()

        max_iterations = 5  # 最多迭代次数
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            try:
                # 调用 LLM
                response = await self.llm.chat(
                    messages=messages,
                    functions=functions,
                    temperature=0.7
                )

                # 检查是否有函数调用
                if hasattr(response, 'function_call') and response.function_call:
                    # LLM 想要调用工具
                    function_name = response.function_call.name
                    function_args = response.function_call.arguments

                    # 解析参数
                    import json
                    args = json.loads(function_args) if isinstance(function_args, str) else function_args

                    print(f"\n🔧 正在调用工具: {function_name}")
                    print(f"   参数: {args}")

                    # 执行工具
                    result = await self.registry.execute_tool(function_name, **args)

                    if result.success:
                        print(f"✅ 工具执行成功")
                    else:
                        print(f"❌ 工具执行失败: {result.error}")

                    # 将工具调用和结果添加到消息历史
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "function_call": {
                            "name": function_name,
                            "arguments": function_args
                        }
                    })

                    messages.append({
                        "role": "function",
                        "name": function_name,
                        "content": json.dumps(result.to_dict(), ensure_ascii=False)
                    })

                    # 继续循环，让 LLM 处理工具结果
                    continue

                else:
                    # LLM 给出了最终回复
                    assistant_message = response.content if hasattr(response, 'content') else str(response)

                    # 添加到历史
                    self.conversation_history.append({
                        "role": "assistant",
                        "content": assistant_message
                    })

                    return assistant_message

            except Exception as e:
                logger.error(f"LLM 调用出错: {e}", exc_info=True)
                return f"抱歉，处理您的请求时出现错误: {str(e)}"

        return "抱歉，处理超时，请尝试重新表述您的请求。"

    async def simple_call_tools(self, user_message: str) -> str:
        """简化版本：直接识别意图并调用工具（不使用 LLM Function Calling）"""
        message_lower = user_message.lower()

        # 简单的关键词匹配
        if any(word in message_lower for word in ['天气', 'weather', '温度', '气温']):
            return await self._handle_weather_query(user_message)
        elif any(word in message_lower for word in ['影像', '卫星', 'satellite', '图片', '下载']):
            return await self._handle_imagery_query(user_message)
        else:
            return "我可以帮您查询天气或获取卫星影像。\n请告诉我您想要:\n1. 查询某个地点的天气\n2. 下载某个地点的卫星影像"

    async def _handle_weather_query(self, message: str) -> str:
        """处理天气查询"""
        # 简单的城市识别
        cities = {
            "北京": (116.4074, 39.9042),
            "上海": (121.4737, 31.2304),
            "广州": (113.2644, 23.1291),
            "深圳": (114.0579, 22.5431),
            "成都": (104.0668, 30.5728),
            "杭州": (120.1551, 30.2741),
        }

        found_city = None
        coords = None

        for city, coord in cities.items():
            if city in message:
                found_city = city
                coords = coord
                break

        if not coords:
            return "请告诉我您想查询哪个城市的天气？（支持：北京、上海、广州、深圳、成都、杭州）"

        print(f"\n🌤️  正在查询 {found_city} 的天气...")

        result = await self.registry.execute_tool(
            "weather_query",
            latitude=coords[1],
            longitude=coords[0]
        )

        if result.success:
            data = result.data['data']
            response = f"\n📍 {found_city} 当前天气:\n"
            response += f"   🌡️  温度: {data.get('temperature_2m')}°C\n"
            response += f"   💧 湿度: {data.get('relative_humidity_2m')}%\n"
            response += f"   🌧️  降水: {data.get('precipitation')} mm\n"
            response += f"   💨 风速: {data.get('wind_speed_10m')} km/h\n"
            response += f"   ⏰ 时间: {data.get('time')}"
            return response
        else:
            return f"抱歉，查询天气失败: {result.error}"

    async def _handle_imagery_query(self, message: str) -> str:
        """处理影像查询"""
        cities = {
            "北京": (116.4074, 39.9042),
            "上海": (121.4737, 31.2304),
            "广州": (113.2644, 23.1291),
            "深圳": (114.0579, 22.5431),
            "成都": (104.0668, 30.5728),
            "杭州": (120.1551, 30.2741),
        }

        found_city = None
        coords = None

        for city, coord in cities.items():
            if city in message:
                found_city = city
                coords = coord
                break

        if not coords:
            return "请告诉我您想下载哪个城市的卫星影像？（支持：北京、上海、广州、深圳、成都、杭州）"

        # 检查是否要保存到文件
        save_to_file = any(word in message for word in ['下载', '保存', '文件', 'save', 'download'])

        print(f"\n🛰️  正在获取 {found_city} 的卫星影像...")

        params = {
            "location": [coords[0], coords[1]],
            "source": "google",
            "zoom_level": 18,
            "point_size": 1000
        }

        if save_to_file:
            params["return_format"] = "file"
            params["output_path"] = "./satellite_images"
            params["filename"] = f"{found_city}_satellite.png"

        result = await self.registry.execute_tool("imagery_query", **params)

        if result.success:
            data = result.data
            response = f"\n📍 {found_city} 卫星影像:\n"
            response += f"   🗺️  数据源: {data.get('source')}\n"
            response += f"   📐 影像尺寸: {data.get('shape')[0]}x{data.get('shape')[1]} 像素\n"

            if save_to_file and 'saved_path' in data:
                response += f"   💾 已保存到: {data.get('saved_path')}\n"
                response += f"   📄 文件名: {data.get('filename')}"
            else:
                response += f"   📊 数据已获取，可以进一步处理"

            return response
        else:
            return f"抱歉，获取影像失败: {result.error}"

    def print_welcome(self):
        """打印欢迎信息"""
        print("\n" + "="*60)
        print("🌍 交互式 GIS Agent")
        print("="*60)
        print("\n功能:")
        print("  1. 🌤️  天气查询 - 查询城市的实时天气")
        print("  2. 🛰️  卫星影像 - 获取/下载卫星图片")
        print("\n支持的城市:")
        print("  北京、上海、广州、深圳、成都、杭州")
        print("\n命令:")
        print("  help  - 显示帮助")
        print("  quit  - 退出程序")
        print("  clear - 清空对话历史")
        print("\n" + "="*60)
        print()

    def print_help(self):
        """打印帮助信息"""
        print("\n" + "="*60)
        print("📖 使用帮助")
        print("="*60)
        print("\n示例:")
        print("  • 查询北京的天气")
        print("  • 下载上海的卫星影像")
        print("  • 深圳现在温度多少")
        print("  • 获取广州的卫星图片并保存")
        print("\n提示:")
        print("  - 直接用自然语言描述您的需求")
        print("  - 支持关键词: 天气、温度、影像、卫星、下载等")
        print("  - 提到'下载'或'保存'会自动保存影像到本地")
        print("="*60 + "\n")

    async def run(self):
        """运行交互式会话"""
        self.print_welcome()

        # 初始化
        print("正在初始化...")

        if not self.initialize_tools():
            return

        print("✅ 工具初始化成功")

        # 尝试初始化 LLM（可选）
        llm_available = self.initialize_llm()

        if llm_available:
            print("✅ LLM 初始化成功 - 使用智能模式")
            use_llm = True
        else:
            print("⚠️  使用简化模式（关键词匹配）")
            print("提示: 配置 OPENAI_API_KEY 可启用智能对话\n")
            use_llm = False

        print("\n开始对话... (输入 'help' 查看帮助, 'quit' 退出)\n")

        # 主循环
        while True:
            try:
                # 获取用户输入
                user_input = input("👤 您: ").strip()

                if not user_input:
                    continue

                # 处理命令
                if user_input.lower() == 'quit':
                    print("\n👋 再见！")
                    break

                if user_input.lower() == 'help':
                    self.print_help()
                    continue

                if user_input.lower() == 'clear':
                    self.conversation_history = []
                    print("✅ 对话历史已清空\n")
                    continue

                # 处理用户请求
                print()  # 空行

                if use_llm:
                    response = await self.call_llm_with_tools(user_input)
                else:
                    response = await self.simple_call_tools(user_input)

                print(f"\n🤖 Agent: {response}\n")

            except KeyboardInterrupt:
                print("\n\n👋 再见！")
                break
            except Exception as e:
                print(f"\n❌ 错误: {e}\n")
                logger.error(f"错误: {e}", exc_info=True)


async def main():
    """主函数"""
    agent = InteractiveGISAgent()
    await agent.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n程序已终止")
