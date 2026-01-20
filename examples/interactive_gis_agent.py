"""
交互式 GIS Agent
在终端中与用户交互，通过 LLM Function Calling 自动分析用户需求并调用天气查询和影像切片工具
"""
import asyncio
import os
import sys
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from swagent.tools import ToolRegistry
from swagent.tools.domain import WeatherTool, ImageryTool, LocationTool
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
        """初始化 LLM（必须）"""
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = os.getenv("DEFAULT_MODEL", "gpt-4")

        if not api_key:
            print("❌ 错误: 未配置 OPENAI_API_KEY 环境变量")
            print("请设置环境变量:")
            print("  export OPENAI_API_KEY='your-api-key'")
            print("  export OPENAI_BASE_URL='your-base-url'  # 可选")
            print("\n⚠️  注意: 本 Agent 需要 LLM 进行智能分析和工具调用")
            raise RuntimeError("LLM 未配置")

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
            raise

    def initialize_tools(self):
        """初始化工具"""
        try:
            # 注册工具
            self.registry.register(LocationTool())  # 地理编码工具（地名转坐标）
            self.registry.register(WeatherTool())   # 天气查询工具
            self.registry.register(ImageryTool())   # 影像查询工具

            logger.info("工具注册成功")
            return True
        except Exception as e:
            print(f"❌ 工具初始化失败: {e}")
            return False

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的 GIS (地理信息系统) 助手，可以帮助用户查询天气和获取卫星影像。

你有以下工具可用：
1. location_geocoding - 将地址/地名转换为经纬度坐标（必须先调用此工具获取坐标）
2. weather_query - 根据坐标查询天气数据（需要经纬度参数）
3. imagery_query - 获取卫星影像（需要经纬度参数）

**重要工作流程**:
当用户提供地名或地址时：
1. 先调用 location_geocoding 获取该地点的经纬度坐标
2. 使用返回的 longitude 和 latitude 参数调用 weather_query 或 imagery_query
3. 整合结果并友好地呈现给用户

当用户直接提供坐标时（如 "51.30, 00.07"）：
1. 直接提取坐标值
2. 调用 weather_query 或 imagery_query
3. 返回结果

**工具参数说明**:
- location_geocoding:
  * address: 地址或地名（如"北京"、"上海东方明珠"、"深圳市南山区"）
  * city: 可选，指定城市范围
  * 返回: longitude (经度), latitude (纬度)

- weather_query:
  * latitude: 纬度（必需）
  * longitude: 经度（必需）
  * when: 可选，查询时间
  * timezone: 可选，时区

- imagery_query:
  * location: [经度, 纬度] 数组格式（必需）
  * source: 数据源，如 "google"
  * zoom_level: 缩放级别，通常 18
  * point_size: 图像范围，通常 1000
  * return_format: "file" 表示保存到文件
  * output_path: 保存路径，如 "./satellite_images"

**示例分析**:

用户: "查询北京的天气"
步骤:
1. 调用 location_geocoding(address="北京")
2. 获取结果: longitude=116.4074, latitude=39.9042
3. 调用 weather_query(latitude=39.9042, longitude=116.4074)
4. 返回天气信息

用户: "下载上海的卫星影像"
步骤:
1. 调用 location_geocoding(address="上海")
2. 获取结果: longitude=121.4737, latitude=31.2304
3. 调用 imagery_query(location=[121.4737, 31.2304], source="google", zoom_level=18, point_size=1000, return_format="file", output_path="./satellite_images")
4. 返回影像信息

用户: "查询(51.30, 00.07)的天气"
步骤:
1. 直接提取坐标: latitude=51.30, longitude=0.07
2. 调用 weather_query(latitude=51.30, longitude=0.07)
3. 返回天气信息

用户: "查询清华大学的天气和影像"
步骤:
1. 调用 location_geocoding(address="清华大学")
2. 获取坐标
3. 调用 weather_query(latitude=..., longitude=...)
4. 调用 imagery_query(location=[...], ...)
5. 整合两个结果并返回

**注意事项**:
- 除非用户直接提供明确的经纬度坐标，否则必须先调用 location_geocoding
- location_geocoding 返回的是 longitude 和 latitude
- imagery_query 的 location 参数顺序是 [经度, 纬度]
- weather_query 的参数顺序是 latitude, longitude

请用中文回复，简洁明了。当你调用工具时，请清晰说明你在做什么。"""

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
                # 调用 LLM（使用新版 tools 格式）
                response = await self.llm.chat(
                    messages=messages,
                    tools=functions,  # 使用 tools 参数（新版格式）
                    tool_choice="auto",
                    temperature=0.7
                )

                # 检查是否有工具调用（新版格式使用 tool_calls）
                if hasattr(response, 'raw_response'):
                    raw_msg = response.raw_response.choices[0].message

                    # 新版格式：检查 tool_calls
                    if hasattr(raw_msg, 'tool_calls') and raw_msg.tool_calls:
                        import json

                        # 获取第一个工具调用
                        tool_call = raw_msg.tool_calls[0]
                        function_name = tool_call.function.name
                        function_args = tool_call.function.arguments

                        # 解析参数
                        args = json.loads(function_args) if isinstance(function_args, str) else function_args

                        print(f"\n🔧 正在调用工具: {function_name}")
                        print(f"   参数: {args}")

                        # 执行工具
                        result = await self.registry.execute_tool(function_name, **args)

                        if result.success:
                            print(f"✅ 工具执行成功")
                        else:
                            print(f"❌ 工具执行失败: {result.error}")

                        # 将工具调用和结果添加到消息历史（新版格式）
                        messages.append({
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [{
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": function_name,
                                    "arguments": function_args
                                }
                            }]
                        })

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result.to_dict(), ensure_ascii=False)
                        })

                        # 继续循环，让 LLM 处理工具结果
                        continue

                # 如果没有工具调用，LLM 给出了最终回复
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

    def print_welcome(self):
        """打印欢迎信息"""
        print("\n" + "="*60)
        print("🌍 交互式 GIS Agent (LLM驱动)")
        print("="*60)
        print("\n功能:")
        print("  1. 🌤️  天气查询 - 查询全球任意位置的实时天气")
        print("  2. 🛰️  卫星影像 - 获取/下载卫星图片")
        print("\n特点:")
        print("  • 🤖 LLM智能分析 - 理解自然语言，自动判断是否需要调用工具")
        print("  • 🌍 全球覆盖 - 支持任意城市名称或经纬度坐标")
        print("  • 🔧 Function Calling - 自动选择和调用合适的工具")
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
        print("\n🤖 LLM 驱动模式")
        print("  Agent 使用大语言模型分析您的自然语言请求")
        print("  自动判断是否需要调用工具，无需记忆特定格式")
        print("\n💬 示例对话:")
        print("  自然提问:")
        print("    • 北京今天天气怎么样？")
        print("    • 我想知道伦敦的气温")
        print("    • 帮我下载上海的卫星地图")
        print("    • 能查一下深圳的天气吗")
        print("\n  坐标查询:")
        print("    • 查询(51.30, 00.07)这个位置的天气")
        print("    • (39.90, 116.40)的天气和影像")
        print("    • 坐标 31.23, 121.47 的卫星图")
        print("\n  闲聊互动:")
        print("    • 你好")
        print("    • 你能做什么？")
        print("    • 支持哪些城市？")
        print("\n🌍 位置格式:")
        print("  • 城市名: 北京、上海、伦敦、纽约等")
        print("  • 坐标: (纬度, 经度) 如 (51.30, 00.07)")
        print("  • LLM 会自动理解并提取位置信息")
        print("\n⚡ 智能特性:")
        print("  • 自动判断是否需要调用工具")
        print("  • 智能理解用户意图")
        print("  • 支持上下文对话")
        print("  • 处理含糊或非正式的表达")
        print("="*60 + "\n")

    async def run(self):
        """运行交互式会话"""
        self.print_welcome()

        # 初始化
        print("正在初始化...")

        if not self.initialize_tools():
            return

        print("✅ 工具初始化成功")

        # 初始化 LLM（必须）
        try:
            self.initialize_llm()
            print("✅ LLM 初始化成功")
        except Exception as e:
            print(f"\n❌ 初始化失败: {e}")
            print("请配置 OPENAI_API_KEY 后重试\n")
            return

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

                # 处理用户请求（使用 LLM Function Calling）
                print()  # 空行
                response = await self.call_llm_with_tools(user_input)
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
