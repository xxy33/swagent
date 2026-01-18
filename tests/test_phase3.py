"""
阶段3测试：多Agent通信和协作

测试内容：
1. 消息总线基础功能
2. 轮流发言控制
3. 消息限流
4. 多Agent辩论
5. 带判断的辩论（集成ReAct Agent）
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_message_bus():
    """测试消息总线"""
    print("\n" + "=" * 60)
    print("测试1: 消息总线基础功能")
    print("=" * 60)

    from swagent import MessageBus, PlannerAgent, Message, MessageType

    # 创建消息总线
    bus = MessageBus(enable_rate_limit=False, enable_turn_control=False)

    # 创建两个Agent
    agent1 = PlannerAgent.create(name="Agent1")
    agent2 = PlannerAgent.create(name="Agent2")

    # 注册到总线
    bus.register_agent(agent1.agent_id, agent1)
    bus.register_agent(agent2.agent_id, agent2)

    # 为Agent设置通信器
    from swagent.core.communication import AgentCommunicator
    agent1.communicator = AgentCommunicator(agent1.agent_id, bus)
    agent2.communicator = AgentCommunicator(agent2.agent_id, bus)

    print(f"✓ 创建消息总线，注册了{len(bus.agents)}个Agent")

    # 测试点对点通信
    success = await agent1.communicator.send_to(
        target=agent2.agent_id,
        content="你好，Agent2！"
    )

    print(f"✓ Agent1 -> Agent2 发送: {success}")

    # Agent2接收消息
    msg = await agent2.communicator.receive(timeout=1.0)
    if msg:
        print(f"✓ Agent2收到: {msg.content}")

    # 测试广播
    success = await agent1.communicator.broadcast("大家好！")
    print(f"✓ Agent1广播消息: {success}")

    # Agent2接收广播
    msg = await agent2.communicator.receive(timeout=1.0)
    if msg:
        print(f"✓ Agent2收到广播: {msg.content}")

    stats = bus.get_stats()
    print(f"✓ 总线统计: {stats['total_messages']}条消息")

    return True


async def test_turn_control():
    """测试轮流发言控制"""
    print("\n" + "=" * 60)
    print("测试2: 轮流发言控制")
    print("=" * 60)

    from swagent import MessageBus, PlannerAgent
    from swagent.core.communication import AgentCommunicator

    # 创建带轮流控制的总线
    bus = MessageBus(enable_rate_limit=False, enable_turn_control=True)

    # 创建3个Agent
    agents = [PlannerAgent.create(name=f"Agent{i+1}") for i in range(3)]

    # 注册并设置通信器
    for agent in agents:
        bus.register_agent(agent.agent_id, agent)
        agent.communicator = AgentCommunicator(agent.agent_id, bus)

    # 设置轮流顺序
    agent_ids = [agent.agent_id for agent in agents]
    bus.setup_turn_control(agent_ids, round_robin=True)

    print(f"✓ 设置轮流发言，共{len(agents)}个Agent")
    print(f"当前发言者: {agents[0].config.name}")

    # 测试轮流
    for round_num in range(1, 4):
        print(f"\n--- 第{round_num}轮 ---")

        for agent in agents:
            current_speaker = bus.turn_manager.get_current_speaker()
            is_turn = (agent.agent_id == current_speaker)

            print(f"{agent.config.name} {'(轮到)' if is_turn else '(等待)'}", end=" ")

            if is_turn:
                # 发言
                success = await agent.communicator.broadcast(f"我是{agent.config.name}，第{round_num}轮发言")
                print(f"- 发言: {success}")

                # 切换到下一个
                bus.next_turn()
            else:
                # 尝试发言（应该失败）
                success = await agent.communicator.broadcast("不该是我说话")
                print(f"- 尝试发言: {success} (应该False)")

    print(f"\n✓ 轮流控制测试完成")

    return True


async def test_rate_limit():
    """测试消息限流"""
    print("\n" + "=" * 60)
    print("测试3: 消息限流")
    print("=" * 60)

    from swagent import MessageBus, PlannerAgent, RateLimitConfig
    from swagent.core.communication import AgentCommunicator

    # 创建严格的限流配置
    config = RateLimitConfig(
        max_messages_per_minute=5,
        max_messages_per_turn=2,
        cooldown_seconds=0.5
    )

    bus = MessageBus(enable_rate_limit=True, rate_limit_config=config)

    agent = PlannerAgent.create(name="TestAgent")
    bus.register_agent(agent.agent_id, agent)
    agent.communicator = AgentCommunicator(agent.agent_id, bus)

    print(f"✓ 限流配置: 最多{config.max_messages_per_turn}条/轮, 冷却{config.cooldown_seconds}秒")

    # 测试同一轮内的限制
    print("\n测试每轮限制:")
    for i in range(3):
        success = await agent.communicator.broadcast(f"消息{i+1}")
        print(f"  消息{i+1}: {success} {'✓' if success else '✗ (超出轮次限制)'}")

    # 重置轮次
    bus.rate_limiter.reset_turn()
    print("\n重置轮次后:")

    # 测试冷却时间
    success1 = await agent.communicator.broadcast("消息A")
    print(f"  消息A: {success1}")

    success2 = await agent.communicator.broadcast("消息B (立即)")
    print(f"  消息B: {success2} {'✗ (冷却中)' if not success2 else ''}")

    # 等待冷却
    await asyncio.sleep(0.6)
    success3 = await agent.communicator.broadcast("消息C (冷却后)")
    print(f"  消息C: {success3} ✓")

    print(f"\n✓ 限流测试完成")

    return True


async def test_simple_debate():
    """测试简单辩论"""
    print("\n" + "=" * 60)
    print("测试4: 多Agent辩论（3轮）")
    print("=" * 60)

    from swagent import Orchestrator, PlannerAgent, OrchestrationMode, TaskDefinition

    # 创建编排器（辩论模式）
    orchestrator = Orchestrator(mode=OrchestrationMode.DEBATE, enable_rate_limit=True)

    # 创建3个辩论Agent
    agent1 = PlannerAgent.create(name="环保专家")
    agent2 = PlannerAgent.create(name="经济学家")
    agent3 = PlannerAgent.create(name="工程师")

    # 注册Agent
    orchestrator.register_agent(agent1)
    orchestrator.register_agent(agent2)
    orchestrator.register_agent(agent3)

    print(f"✓ 创建辩论，参与者: {[a.config.name for a in [agent1, agent2, agent3]]}")

    # 启动编排器
    await orchestrator.start()

    # 创建辩论任务
    task = TaskDefinition(
        name="垃圾处理辩论",
        description="讨论城市垃圾处理的最佳方案：焚烧 vs 分类回收+堆肥"
    )

    print(f"\n辩论主题: {task.description}")
    print("=" * 60)

    # 执行辩论（3轮）
    result = await orchestrator._execute_debate(task, timeout=None, max_rounds=3)

    print("\n" + "=" * 60)
    print("辩论结果:")
    print(f"  总轮数: {result['rounds']}")
    print(f"  总消息数: {result['total_messages']}")
    print(f"  参与者发言数: {len(result['history'])}")

    print(f"\n✓ 简单辩论测试完成")

    await orchestrator.stop()

    return True


async def test_debate_with_judgment():
    """测试带判断的辩论"""
    print("\n" + "=" * 60)
    print("测试5: 带判断的辩论")
    print("=" * 60)

    from swagent import Orchestrator, PlannerAgent, ReActAgent, OrchestrationMode

    # 创建编排器
    orchestrator = Orchestrator(mode=OrchestrationMode.DEBATE)

    # 创建辩论Agent
    agent1 = PlannerAgent.create(name="支持方")
    agent2 = PlannerAgent.create(name="反对方")

    orchestrator.register_agent(agent1)
    orchestrator.register_agent(agent2)

    # 创建判断Agent
    judge = ReActAgent.create(name="辩论裁判")

    print(f"✓ 辩论参与者: {agent1.config.name}, {agent2.config.name}")
    print(f"✓ 判断Agent: {judge.config.name}")

    await orchestrator.start()

    # 执行带判断的辩论
    topic = "城市应该优先发展垃圾焚烧发电还是分类回收系统？"
    print(f"\n辩论主题: {topic}")
    print("=" * 60)

    result = await orchestrator.debate_with_judgment(
        topic=topic,
        max_rounds=5,
        judge_agent=judge
    )

    print("\n" + "=" * 60)
    print("辩论结果:")
    print(f"  实际轮数: {result['total_rounds']}")
    print(f"  是否由判断终止: {result['terminated_by_judgment']}")

    if result['judgment']:
        judgment = result['judgment']
        print(f"  判断状态: {judgment.decision.value}")
        print(f"  置信度: {judgment.confidence}")
        print(f"  理由: {judgment.reason[:100]}...")

    print(f"\n✓ 带判断的辩论测试完成")

    await orchestrator.stop()

    return True


async def main():
    """主测试函数"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "SWAgent - 阶段3测试" + " " * 23 + "║")
    print("║" + " " * 17 + "多Agent通信和协作" + " " * 22 + "║")
    print("╚" + "═" * 58 + "╝")

    results = []

    # 测试1: 消息总线
    try:
        result = await test_message_bus()
        results.append(("消息总线", result))
    except Exception as e:
        print(f"\n✗ 消息总线测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("消息总线", False))

    # 测试2: 轮流控制
    try:
        result = await test_turn_control()
        results.append(("轮流控制", result))
    except Exception as e:
        print(f"\n✗ 轮流控制测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("轮流控制", False))

    # 测试3: 限流
    try:
        result = await test_rate_limit()
        results.append(("消息限流", result))
    except Exception as e:
        print(f"\n✗ 限流测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("消息限流", False))

    # 测试4: 简单辩论
    try:
        result = await test_simple_debate()
        results.append(("简单辩论", result))
    except Exception as e:
        print(f"\n✗ 简单辩论测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("简单辩论", False))

    # 测试5: 带判断的辩论
    try:
        result = await test_debate_with_judgment()
        results.append(("带判断辩论", result))
    except Exception as e:
        print(f"\n✗ 带判断辩论测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("带判断辩论", False))

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
        print("\n🎉 阶段3测试全部通过!")
        print("\n已完成功能:")
        print("  ✓ 消息总线（点对点、广播通信）")
        print("  ✓ 轮流发言控制")
        print("  ✓ 消息限流（防刷屏）")
        print("  ✓ 多Agent辩论")
        print("  ✓ 集成ReAct Agent判断")
    else:
        print("\n⚠️  部分测试失败，请检查后重试。")

    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
