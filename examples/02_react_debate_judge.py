"""
ReAct Agent使用示例
演示如何使用ReAct Agent判断多Agent辩论何时终止
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from swagent.agents.react_agent import ReActAgent, DebateStatus


async def simulate_debate():
    """模拟一个多Agent辩论场景"""
    print("=" * 70)
    print("场景：多Agent辩论 - 城市垃圾处理方案选择")
    print("=" * 70)
    print()

    # 创建ReAct判断Agent
    judge = ReActAgent.create(name="辩论裁判")

    print(f"✓ 创建判断Agent: {judge.config.name}")
    print()

    # 模拟辩论历史（3个Agent讨论垃圾处理方案）
    debates = [
        # 第1轮
        [
            {"agent": "环保专家", "content": "我强烈建议采用分类回收+堆肥的方案，这是最环保的。"},
            {"agent": "经济学家", "content": "但回收和堆肥的成本很高，建议考虑焚烧发电方案。"},
            {"agent": "工程师", "content": "焚烧技术现在很成熟，而且能产生经济效益。"}
        ],
        # 第2轮
        [
            {"agent": "环保专家", "content": "我强烈建议采用分类回收+堆肥的方案，这是最环保的。"},
            {"agent": "经济学家", "content": "但回收和堆肥的成本很高，建议考虑焚烧发电方案。"},
            {"agent": "工程师", "content": "焚烧技术现在很成熟，而且能产生经济效益。"},
            {"agent": "环保专家", "content": "焚烧会产生污染，即使有过滤设备也不能100%消除。"},
            {"agent": "经济学家", "content": "从成本效益角度，焚烧确实更优。初期投资大，但长期收益高。"},
            {"agent": "工程师", "content": "我同意，现代焚烧厂的排放标准很严格，污染可控。"}
        ],
        # 第3轮
        [
            {"agent": "环保专家", "content": "我强烈建议采用分类回收+堆肥的方案，这是最环保的。"},
            {"agent": "经济学家", "content": "但回收和堆肥的成本很高，建议考虑焚烧发电方案。"},
            {"agent": "工程师", "content": "焚烧技术现在很成熟，而且能产生经济效益。"},
            {"agent": "环保专家", "content": "焚烧会产生污染，即使有过滤设备也不能100%消除。"},
            {"agent": "经济学家", "content": "从成本效益角度，焚烧确实更优。初期投资大，但长期收益高。"},
            {"agent": "工程师", "content": "我同意，现代焚烧厂的排放标准很严格，污染可控。"},
            {"agent": "环保专家", "content": "我理解经济考量，但也许我们可以结合两种方案？"},
            {"agent": "经济学家", "content": "这个想法不错。分类回收处理可回收物，剩余的焚烧。"},
            {"agent": "工程师", "content": "对，混合方案可以平衡环保和经济性。我支持这个方向。"}
        ]
    ]

    # 逐轮判断
    for round_num, debate_history in enumerate(debates, 1):
        print("-" * 70)
        print(f"第 {round_num} 轮讨论后判断")
        print("-" * 70)
        print()

        # 显示本轮新增的发言
        if round_num == 1:
            new_messages = debate_history
        else:
            prev_count = len(debates[round_num - 2])
            new_messages = debate_history[prev_count:]

        print("新增发言:")
        for msg in new_messages:
            print(f"  [{msg['agent']}]: {msg['content']}")
        print()

        # 判断是否应该终止
        should_stop, result = await judge.should_terminate_debate(
            debate_history=debate_history,
            current_round=round_num,
            max_rounds=5,
            min_confidence=0.7
        )

        print("判断结果:")
        print(f"  状态: {result.decision.value}")
        print(f"  置信度: {result.confidence:.2f}")
        print(f"  是否终止: {'是' if should_stop else '否'}")
        print()
        print("决策理由:")
        print(f"  {result.reason}")
        print()

        if result.suggestions:
            print("建议:")
            for suggestion in result.suggestions:
                print(f"  - {suggestion}")
            print()

        if should_stop:
            print("🎯 辩论达到终止条件，建议结束讨论。")
            break
    else:
        print("⚠️  达到最大轮次，但未达成明确结论。")

    print()
    print("=" * 70)


async def analyze_consensus_example():
    """共识分析示例"""
    print("\n" + "=" * 70)
    print("功能演示：共识分析")
    print("=" * 70)
    print()

    judge = ReActAgent.create()

    # 一个部分达成共识的讨论
    debate = [
        {"agent": "专家A", "content": "垃圾分类是基础，这点毫无疑问。"},
        {"agent": "专家B", "content": "同意，但具体分几类我认为需要因地制宜。"},
        {"agent": "专家C", "content": "我建议统一标准，便于管理和宣传。"},
        {"agent": "专家A", "content": "统一标准确实有利于推广，但也要考虑地方差异。"},
        {"agent": "专家B", "content": "可以有国家标准，允许地方在此基础上调整。"},
        {"agent": "专家C", "content": "这个折中方案不错，既有标准又有灵活性。"}
    ]

    print("分析以下讨论的共识程度...")
    print()

    result = await judge.analyze_consensus(debate)

    print("共识分析结果:")
    print("-" * 70)
    print(result["analysis"])
    print("-" * 70)
    print()


async def main():
    """主函数"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 20 + "ReAct Agent 使用示例" + " " * 28 + "║")
    print("║" + " " * 22 + "辩论终止判断" + " " * 32 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    # 示例1: 模拟辩论判断
    await simulate_debate()

    # 示例2: 共识分析
    await analyze_consensus_example()

    print("\n✅ 示例运行完成")
    print()
    print("ReAct Agent主要功能:")
    print("  1. 判断多Agent辩论何时应该终止")
    print("  2. 识别达成共识、分歧过大等场景")
    print("  3. 提供清晰的决策理由和建议")
    print("  4. 分析讨论的共识程度")
    print()


if __name__ == "__main__":
    asyncio.run(main())
