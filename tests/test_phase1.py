"""
阶段1测试：LLM接口层测试

测试内容：
1. 配置系统
2. 日志系统
3. OpenAI兼容客户端连接

使用前请配置：
1. 在项目根目录创建.env文件
2. 添加: OPENAI_API_KEY=your_api_key_here
3. 如需修改base_url，请修改config.yaml中的llm.providers.openai.base_url
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_config():
    """测试配置系统"""
    print("\n" + "=" * 60)
    print("测试1: 配置系统")
    print("=" * 60)

    from swagent.utils.config import get_config

    config = get_config()

    print(f"✓ 应用名称: {config.get('app.name')}")
    print(f"✓ 应用版本: {config.get('app.version')}")
    print(f"✓ 默认LLM提供商: {config.get('llm.default_provider')}")

    llm_config = config.get_llm_config()
    print(f"✓ LLM模型: {llm_config.get('default_model')}")
    print(f"✓ Base URL: {llm_config.get('base_url')}")
    print(f"✓ API Key已配置: {'是' if llm_config.get('api_key') else '否'}")

    return True


async def test_logger():
    """测试日志系统"""
    print("\n" + "=" * 60)
    print("测试2: 日志系统")
    print("=" * 60)

    from swagent.utils.logger import get_logger

    logger = get_logger("test")

    logger.debug("这是DEBUG日志")
    logger.info("这是INFO日志")
    logger.warning("这是WARNING日志")

    print("✓ 日志系统工作正常")

    return True


async def test_llm_connection():
    """测试LLM连接"""
    print("\n" + "=" * 60)
    print("测试3: LLM连接测试")
    print("=" * 60)

    from swagent.llm.openai_client import OpenAIClient

    try:
        # 从配置文件创建客户端
        client = OpenAIClient.from_config_file()

        print(f"✓ 客户端创建成功")
        print(f"  - 提供商: {client.provider}")
        print(f"  - 模型: {client.model_name}")
        print(f"  - Base URL: {client.config.base_url}")

        # 发送测试消息
        print("\n发送测试消息...")
        messages = [
            {"role": "user", "content": "你好，请用一句话介绍你自己。"}
        ]

        response = await client.chat(messages)

        print(f"\n✓ LLM响应成功!")
        print(f"  - 模型: {response.model}")
        print(f"  - Token使用: {response.total_tokens} (输入: {response.prompt_tokens}, 输出: {response.completion_tokens})")
        print(f"  - 完成原因: {response.finish_reason}")
        print(f"\n回复内容:\n{response.content}")

        return True

    except Exception as e:
        print(f"\n✗ LLM连接测试失败: {str(e)}")
        print("\n请检查:")
        print("1. .env文件中是否配置了OPENAI_API_KEY")
        print("2. config.yaml中的base_url是否正确")
        print("3. 网络连接是否正常")
        return False


async def test_llm_stream():
    """测试流式响应"""
    print("\n" + "=" * 60)
    print("测试4: LLM流式响应测试")
    print("=" * 60)

    from swagent.llm.openai_client import OpenAIClient

    try:
        client = OpenAIClient.from_config_file()

        print("发送流式请求...")
        messages = [
            {"role": "user", "content": "用一句话说明什么是人工智能。"}
        ]

        print("\n流式响应内容:")
        print("-" * 60)

        full_response = ""
        async for chunk in client.chat_stream(messages):
            print(chunk, end="", flush=True)
            full_response += chunk

        print("\n" + "-" * 60)
        print(f"\n✓ 流式响应成功! (共{len(full_response)}字符)")

        return True

    except Exception as e:
        print(f"\n✗ 流式响应测试失败: {str(e)}")
        return False


async def main():
    """主测试函数"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "SWAgent - 阶段1测试" + " " * 23 + "║")
    print("║" + " " * 20 + "LLM接口层" + " " * 28 + "║")
    print("╚" + "═" * 58 + "╝")

    results = []

    # 测试1: 配置系统
    try:
        result = await test_config()
        results.append(("配置系统", result))
    except Exception as e:
        print(f"\n✗ 配置系统测试失败: {str(e)}")
        results.append(("配置系统", False))

    # 测试2: 日志系统
    try:
        result = await test_logger()
        results.append(("日志系统", result))
    except Exception as e:
        print(f"\n✗ 日志系统测试失败: {str(e)}")
        results.append(("日志系统", False))

    # 测试3: LLM连接
    try:
        result = await test_llm_connection()
        results.append(("LLM连接", result))
    except Exception as e:
        print(f"\n✗ LLM连接测试出错: {str(e)}")
        results.append(("LLM连接", False))

    # 测试4: 流式响应（可选）
    try:
        result = await test_llm_stream()
        results.append(("流式响应", result))
    except Exception as e:
        print(f"\n✗ 流式响应测试出错: {str(e)}")
        results.append(("流式响应", False))

    # 测试总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{name}: {status}")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 阶段1测试全部通过! 可以继续阶段2。")
    else:
        print("\n⚠️  部分测试失败，请检查配置后重试。")

    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
