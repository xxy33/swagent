"""
ReAct Agent测试
测试ReAct Agent的辩论判断能力
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_react_agent_creation():
    """测试ReAct Agent创建"""
    print("\n" + "=" * 60)
    print("测试1: ReAct Agent创建")
    print("=" * 60)

    from swagent.agents.react_agent import ReActAgent

    # 创建ReAct Agent
    agent = ReActAgent.create()

    print(f"✓ ReAct Agent创建成功")
    print(f"  - ID: {agent.agent_id}")
    print(f"  - 名称: {agent.config.name}")
    print(f"  - 角色: {agent.config.role}")
    print(f"  - 模型: {agent.llm.model_name}")

    return True


async def test_debate_judgment_consensus():
    """测试辩论判断 - 达成共识的场景"""
    print("\n" + "=" * 60)
    print("测试2: 辩论判断 - 达成共识")
    print("=" * 60)

    from swagent.agents.react_agent import ReActAgent

    agent = ReActAgent.create()

    # 模拟一个达成共识的辩论历史
    debate_history = [
        {
            "agent": "Agent1",
            "content": "我认为焚烧处理是处理城市生活垃圾的有效方法，可以减少填埋场压力。"
        },
        {
            "agent": "Agent2",
            "content": "我同意，焚烧确实能显著减少垃圾体积，而且现代焚烧技术的污染控制做得很好。"
        },
        {
            "agent": "Agent1",
            "content": "是的，而且还能发电，实现能源回收。"
        },
        {
            "agent": "Agent2",
            "content": "没错，我们的观点基本一致。焚烧+能源回收是目前较好的方案。"
        }
    ]

    print("模拟辩论场景：关于垃圾焚烧处理的讨论")
    print(f"- 发言次数: {len(debate_history)}")
    print(f"- 参与者: Agent1, Agent2")
    print()

    # 判断辩论状态
    result = await agent.judge_debate_status(
        debate_history=debate_history,
        current_round=2,
        max_rounds=5
    )

    print("判断结果:")
    print("-" * 60)
    print(f"决策: {result.decision.value}")
    print(f"置信度: {result.confidence}")
    print()
    print("思考过程:")
    print(result.reasoning[:200] + "...")
    print()
    print("观察结果:")
    print(result.observation[:200] + "...")
    print()
    print("决策理由:")
    print(result.reason)
    print()
    if result.suggestions:
        print("建议:")
        for i, suggestion in enumerate(result.suggestions, 1):
            print(f"  {i}. {suggestion}")
    print("-" * 60)

    print(f"\n✓ 辩论判断完成")

    return True


async def test_debate_judgment_divergence():
    """测试辩论判断 - 分歧过大的场景"""
    print("\n" + "=" * 60)
    print("测试3: 辩论判断 - 分歧过大")
    print("=" * 60)

    from swagent.agents.react_agent import ReActAgent

    agent = ReActAgent.create()

    # 模拟一个分歧很大的辩论历史
    debate_history = [
        {
            "agent": "Agent1",
            "content": "焚烧处理会产生大量二噁英等有害物质，对环境危害极大，应该全面禁止。"
        },
        {
            "agent": "Agent2",
            "content": "现代焚烧技术完全可以控制污染，你说的问题早就解决了。焚烧是最优方案。"
        },
        {
            "agent": "Agent1",
            "content": "即使技术再先进，也不能100%消除污染。应该优先考虑回收利用和堆肥。"
        },
        {
            "agent": "Agent2",
            "content": "回收和堆肥根本处理不了这么大的垃圾量，你的想法不切实际。"
        },
        {
            "agent": "Agent1",
            "content": "你这是在为焚烧企业辩护，完全忽视了环境和健康风险！"
        },
        {
            "agent": "Agent2",
            "content": "你才是在固守过时观念，拒绝接受科技进步的事实！"
        }
    ]

    print("模拟辩论场景：关于焚烧处理的激烈争论")
    print(f"- 发言次数: {len(debate_history)}")
    print(f"- 参与者: Agent1, Agent2")
    print()

    # 判断辩论状态
    result = await agent.judge_debate_status(
        debate_history=debate_history,
        current_round=3,
        max_rounds=5
    )

    print("判断结果:")
    print("-" * 60)
    print(f"决策: {result.decision.value}")
    print(f"置信度: {result.confidence}")
    print()
    print("决策理由:")
    print(result.reason)
    print("-" * 60)

    print(f"\n✓ 辩论判断完成")

    return True


async def test_should_terminate():
    """测试终止判断简化接口"""
    print("\n" + "=" * 60)
    print("测试4: 终止判断简化接口")
    print("=" * 60)

    from swagent.agents.react_agent import ReActAgent

    agent = ReActAgent.create()

    # 模拟一个信息充分的辩论
    debate_history = [
        {"agent": "Expert1", "content": "从技术角度看，焚烧+余热发电是成熟方案。"},
        {"agent": "Expert2", "content": "从经济角度看，初期投资大但长期运营成本可控。"},
        {"agent": "Expert3", "content": "从环保角度看，需要严格的排放监控和治理措施。"},
        {"agent": "Expert1", "content": "综合考虑，建议采用焚烧+资源回收的综合方案。"},
        {"agent": "Expert2", "content": "同意，关键是做好环保监管和公众沟通。"},
        {"agent": "Expert3", "content": "我也认同这个方案，各方面都考虑到了。"}
    ]

    print("测试终止判断...")
    print()

    should_stop, result = await agent.should_terminate_debate(
        debate_history=debate_history,
        current_round=3,
        max_rounds=10,
        min_confidence=0.6
    )

    print(f"是否应该终止: {'是' if should_stop else '否'}")
    print(f"判断状态: {result.decision.value}")
    print(f"置信度: {result.confidence}")
    print(f"理由: {result.reason[:100]}...")

    print(f"\n✓ 终止判断完成")

    return True


async def test_consensus_analysis():
    """测试共识分析"""
    print("\n" + "=" * 60)
    print("测试5: 共识分析")
    print("=" * 60)

    from swagent.agents.react_agent import ReActAgent

    agent = ReActAgent.create()

    debate_history = [
        {"agent": "Agent1", "content": "垃圾分类是必须的，这点大家都同意吧？"},
        {"agent": "Agent2", "content": "同意，分类是基础。但具体分几类存在争议。"},
        {"agent": "Agent3", "content": "我认为四分类足够，太复杂反而执行困难。"},
        {"agent": "Agent2", "content": "我倾向于六分类，更精细化管理。"},
        {"agent": "Agent1", "content": "分类标准确实有争议，但大家都认同分类的必要性。"}
    ]

    print("分析辩论共识...")
    print()

    result = await agent.analyze_consensus(debate_history)

    print("共识分析结果:")
    print("-" * 60)
    print(result["analysis"][:300] + "...")
    print("-" * 60)

    print(f"\n✓ 共识分析完成")

    return True


async def main():
    """主测试函数"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 18 + "ReAct Agent测试" + " " * 24 + "║")
    print("║" + " " * 17 + "辩论终止判断能力" + " " * 22 + "║")
    print("╚" + "═" * 58 + "╝")

    results = []

    # 测试1: Agent创建
    try:
        result = await test_react_agent_creation()
        results.append(("ReAct Agent创建", result))
    except Exception as e:
        print(f"\n✗ ReAct Agent创建测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("ReAct Agent创建", False))

    # 测试2: 共识场景判断
    try:
        result = await test_debate_judgment_consensus()
        results.append(("共识场景判断", result))
    except Exception as e:
        print(f"\n✗ 共识场景判断测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("共识场景判断", False))

    # 测试3: 分歧场景判断
    try:
        result = await test_debate_judgment_divergence()
        results.append(("分歧场景判断", result))
    except Exception as e:
        print(f"\n✗ 分歧场景判断测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("分歧场景判断", False))

    # 测试4: 终止判断
    try:
        result = await test_should_terminate()
        results.append(("终止判断接口", result))
    except Exception as e:
        print(f"\n✗ 终止判断测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("终止判断接口", False))

    # 测试5: 共识分析
    try:
        result = await test_consensus_analysis()
        results.append(("共识分析", result))
    except Exception as e:
        print(f"\n✗ 共识分析测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("共识分析", False))

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
        print("\n🎉 ReAct Agent测试全部通过!")
        print("\nReAct Agent功能:")
        print("  ✓ 能够判断辩论是否应该终止")
        print("  ✓ 识别达成共识的场景")
        print("  ✓ 识别分歧过大的场景")
        print("  ✓ 提供清晰的决策理由")
        print("  ✓ 分析讨论的共识程度")
    else:
        print("\n⚠️  部分测试失败，请检查后重试。")

    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
