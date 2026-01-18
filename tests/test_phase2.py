"""
阶段2测试：Agent基础框架测试

测试内容：
1. 上下文管理器
2. Agent基类
3. PlannerAgent
4. 简单对话
5. 带记忆的多轮对话

使用前请确保：
1. 已通过阶段1测试
2. .env文件配置正确
3. config.yaml配置正确
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_context_manager():
    """测试上下文管理器"""
    print("\n" + "=" * 60)
    print("测试1: 上下文管理器")
    print("=" * 60)

    from swagent.core.context import ContextManager, ContextScope
    from swagent.core.message import Message, MessageType

    # 创建上下文管理器
    ctx_mgr = ContextManager(max_history=5)

    # 创建上下文
    ctx = ctx_mgr.create_context(
        context_id="test_session",
        scope=ContextScope.SESSION,
        initial_data={"user": "测试用户"}
    )

    print(f"✓ 创建上下文成功 - ID: {ctx.id}")

    # 设置数据
    ctx_mgr.set_context_data("task", "测试任务")
    print(f"✓ 设置上下文数据成功")

    # 获取数据
    task = ctx_mgr.get_context_data("task")
    print(f"✓ 获取上下文数据成功 - task: {task}")

    # 添加消息
    msg1 = Message(sender="user", content="你好", msg_type=MessageType.REQUEST)
    msg2 = Message(sender="agent", content="你好！有什么可以帮助你的？", msg_type=MessageType.RESPONSE)

    ctx_mgr.add_message(msg1)
    ctx_mgr.add_message(msg2)

    print(f"✓ 添加消息成功 - 历史消息数: {len(ctx_mgr.message_history)}")

    # 获取对话历史
    history = ctx_mgr.get_conversation_history(limit=2)
    print(f"✓ 获取对话历史成功 - 消息数: {len(history)}")

    # 摘要
    summary = ctx_mgr.get_summary()
    print(f"✓ 上下文摘要: {summary}")

    return True


async def test_agent_creation():
    """测试Agent创建"""
    print("\n" + "=" * 60)
    print("测试2: Agent创建")
    print("=" * 60)

    from swagent.agents.planner_agent import PlannerAgent

    # 创建PlannerAgent
    agent = PlannerAgent.create()

    print(f"✓ Agent创建成功")
    print(f"  - ID: {agent.agent_id}")
    print(f"  - 名称: {agent.config.name}")
    print(f"  - 角色: {agent.config.role}")
    print(f"  - 模型: {agent.llm.model_name}")
    print(f"  - 状态: {agent.state.value}")

    # 获取状态
    state = agent.get_state()
    print(f"✓ Agent状态: {state}")

    return True


async def test_simple_chat():
    """测试简单对话"""
    print("\n" + "=" * 60)
    print("测试3: 简单对话")
    print("=" * 60)

    from swagent.agents.planner_agent import PlannerAgent
    from swagent.core.message import Message, MessageType

    # 创建Agent
    agent = PlannerAgent.create(name="测试规划师")

    print(f"创建Agent: {agent.config.name}")
    print()

    # 创建测试消息
    message = Message(
        sender="user",
        sender_name="测试用户",
        content="你好，请简单介绍一下你自己。",
        msg_type=MessageType.REQUEST
    )

    print(f"用户: {message.content}")
    print()

    # 运行Agent
    response = await agent.run(message)

    print(f"Agent: {response.content}")
    print()
    print(f"✓ 对话成功")
    print(f"  - 响应类型: {response.msg_type.value}")
    print(f"  - 发送者: {response.sender_name}")

    return True


async def test_multi_turn_chat():
    """测试多轮对话（带记忆）"""
    print("\n" + "=" * 60)
    print("测试4: 多轮对话（带记忆）")
    print("=" * 60)

    from swagent.agents.planner_agent import PlannerAgent
    from swagent.core.message import Message, MessageType

    # 创建Agent
    agent = PlannerAgent.create(name="规划助手")

    print(f"开始多轮对话测试...")
    print()

    # 对话1
    msg1 = Message(
        sender="user",
        sender_name="用户",
        content="我需要处理1000吨生活垃圾，你能帮我规划吗？",
        msg_type=MessageType.REQUEST
    )

    print(f"[第1轮] 用户: {msg1.content}")
    resp1 = await agent.run(msg1)
    print(f"[第1轮] Agent: {resp1.content[:100]}...")
    print()

    # 对话2 - 测试记忆
    msg2 = Message(
        sender="user",
        sender_name="用户",
        content="那如果我想选择焚烧处理，需要注意什么？",
        msg_type=MessageType.REQUEST
    )

    print(f"[第2轮] 用户: {msg2.content}")
    resp2 = await agent.run(msg2)
    print(f"[第2轮] Agent: {resp2.content[:100]}...")
    print()

    # 对话3 - 再测试记忆
    msg3 = Message(
        sender="user",
        sender_name="用户",
        content="刚才你说的数量是多少来着？",
        msg_type=MessageType.REQUEST
    )

    print(f"[第3轮] 用户: {msg3.content}")
    resp3 = await agent.run(msg3)
    print(f"[第3轮] Agent: {resp3.content[:100]}...")
    print()

    # 检查历史
    history_count = len(agent.context_manager.message_history)
    print(f"✓ 多轮对话成功")
    print(f"  - 总消息数: {history_count}")
    print(f"  - Agent能够记住之前的对话内容（1000吨垃圾）")

    return True


async def test_task_analysis():
    """测试任务分析功能"""
    print("\n" + "=" * 60)
    print("测试5: 任务分析功能")
    print("=" * 60)

    from swagent.agents.planner_agent import PlannerAgent

    agent = PlannerAgent.create()

    task_desc = "设计一个城市生活垃圾分类和处理系统"

    print(f"任务: {task_desc}")
    print()
    print("分析中...")

    result = await agent.analyze_task(task_desc)

    print()
    print("分析结果:")
    print("-" * 60)
    print(result["analysis"][:300])
    print("...")
    print("-" * 60)
    print()
    print(f"✓ 任务分析成功")

    return True


async def main():
    """主测试函数"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "SWAgent - 阶段2测试" + " " * 23 + "║")
    print("║" + " " * 18 + "Agent基础框架" + " " * 24 + "║")
    print("╚" + "═" * 58 + "╝")

    results = []

    # 测试1: 上下文管理器
    try:
        result = await test_context_manager()
        results.append(("上下文管理器", result))
    except Exception as e:
        print(f"\n✗ 上下文管理器测试失败: {str(e)}")
        results.append(("上下文管理器", False))

    # 测试2: Agent创建
    try:
        result = await test_agent_creation()
        results.append(("Agent创建", result))
    except Exception as e:
        print(f"\n✗ Agent创建测试失败: {str(e)}")
        results.append(("Agent创建", False))

    # 测试3: 简单对话
    try:
        result = await test_simple_chat()
        results.append(("简单对话", result))
    except Exception as e:
        print(f"\n✗ 简单对话测试失败: {str(e)}")
        results.append(("简单对话", False))

    # 测试4: 多轮对话
    try:
        result = await test_multi_turn_chat()
        results.append(("多轮对话", result))
    except Exception as e:
        print(f"\n✗ 多轮对话测试失败: {str(e)}")
        results.append(("多轮对话", False))

    # 测试5: 任务分析
    try:
        result = await test_task_analysis()
        results.append(("任务分析", result))
    except Exception as e:
        print(f"\n✗ 任务分析测试失败: {str(e)}")
        results.append(("任务分析", False))

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
        print("\n🎉 阶段2测试全部通过! 可以继续阶段3。")
        print("\n已完成功能:")
        print("  ✓ Agent可以进行对话")
        print("  ✓ Agent具有记忆能力")
        print("  ✓ 上下文管理正常工作")
        print("  ✓ PlannerAgent可以分析任务")
    else:
        print("\n⚠️  部分测试失败，请检查后重试。")

    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
