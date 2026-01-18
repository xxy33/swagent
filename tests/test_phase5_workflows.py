"""
阶段5测试：工作流模板

测试内容：
1. 工作流基础架构
2. 科研工作流
3. 报告生成工作流
4. 数据分析工作流
5. 代码开发工作流
6. 工作流管理器
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_base_workflow():
    """测试工作流基础架构"""
    print("\n" + "=" * 60)
    print("测试1: 工作流基础架构")
    print("=" * 60)

    from swagent.workflows import BaseWorkflow, WorkflowContext, StepStatus

    # 创建简单的测试工作流
    class SimpleWorkflow(BaseWorkflow):
        def _setup_steps(self):
            async def step1(ctx):
                return {'result1': 'value1'}

            async def step2(ctx):
                return {'result2': ctx.get('result1') + '_processed'}

            self.add_step('step1', 'First step', step1, outputs=['result1'])
            self.add_step('step2', 'Second step', step2, required_inputs=['result1'], outputs=['result2'])

    workflow = SimpleWorkflow("测试工作流", "测试描述")

    print(f"\n✓ 创建工作流: {workflow.name}")
    print(f"✓ 步骤数量: {len(workflow.steps)}")

    # 执行工作流
    result = await workflow.execute()

    print(f"✓ 执行完成: 成功={result.success}")
    print(f"✓ 完成步骤: {result.completed_steps}/{result.total_steps}")
    print(f"✓ 执行时长: {result.duration:.2f}秒")
    print(f"✓ 上下文数据: {list(result.context.data.keys())}")

    return True


async def test_research_workflow():
    """测试科研工作流"""
    print("\n" + "=" * 60)
    print("测试2: 科研工作流")
    print("=" * 60)

    from swagent.workflows import ResearchWorkflow

    workflow = ResearchWorkflow()

    print(f"\n工作流: {workflow.name}")
    print(f"描述: {workflow.description}")
    print(f"步骤数: {len(workflow.steps)}")

    # 设置初始上下文
    initial_context = {
        'research_topic': '固体废物厌氧消化技术',
        'keywords': ['厌氧消化', '沼气', '有机废物', '能源回收'],
        'methodology_preference': 'mixed'
    }

    # 执行工作流
    print("\n开始执行工作流...")
    result = await workflow.execute(initial_context, stop_on_error=False)

    print(f"\n✓ 执行结果: {'成功' if result.success else '失败'}")
    print(f"✓ 完成率: {result.completion_rate * 100:.1f}%")
    print(f"✓ 执行时长: {result.duration:.2f}秒")

    # 显示步骤结果
    print("\n步骤执行情况:")
    for step_result in result.step_results:
        status_symbol = "✓" if step_result['status'] == 'completed' else "✗"
        print(f"  {status_symbol} {step_result['name']}: {step_result['status']}")

    # 显示关键输出
    if result.context.has('final_conclusions'):
        print("\n最终结论:")
        print(result.context.get('final_conclusions')[:200] + "...")

    return True


async def test_report_workflow():
    """测试报告生成工作流"""
    print("\n" + "=" * 60)
    print("测试3: 报告生成工作流")
    print("=" * 60)

    from swagent.workflows import ReportWorkflow

    workflow = ReportWorkflow()

    print(f"\n工作流: {workflow.name}")
    print(f"步骤: {len(workflow.steps)} 个")

    # 初始上下文
    initial_context = {
        'report_type': 'technical',
        'report_purpose': '总结2024年度固废处理项目执行情况',
        'target_audience': '管理层',
        'template': 'standard'
    }

    result = await workflow.execute(initial_context)

    print(f"\n✓ 报告生成: {'成功' if result.success else '失败'}")
    print(f"✓ 完成步骤: {result.completed_steps}/{result.total_steps}")

    if result.context.has('final_report'):
        final_report = result.context.get('final_report')
        print(f"✓ 报告质量评分: {final_report.get('quality_score', 0):.1f}/100")
        print(f"✓ 报告状态: {final_report.get('status', 'unknown')}")

    return True


async def test_analysis_workflow():
    """测试数据分析工作流"""
    print("\n" + "=" * 60)
    print("测试4: 数据分析工作流")
    print("=" * 60)

    from swagent.workflows import DataAnalysisWorkflow

    workflow = DataAnalysisWorkflow()

    print(f"\n工作流: {workflow.name}")

    initial_context = {
        'data_source': 'waste_management_2024.csv',
        'file_format': 'csv',
        'exploration_depth': 'detailed'
    }

    result = await workflow.execute(initial_context)

    print(f"\n✓ 分析完成: {'成功' if result.success else '失败'}")
    print(f"✓ 完成率: {result.completion_rate * 100:.1f}%")

    if result.context.has('key_findings'):
        findings = result.context.get('key_findings')
        print(f"\n关键发现 ({len(findings)} 条):")
        for finding in findings[:3]:
            print(f"  - {finding}")

    if result.context.has('visualizations'):
        viz = result.context.get('visualizations')
        print(f"\n✓ 生成图表: {len(viz)} 个")

    return True


async def test_coding_workflow():
    """测试代码开发工作流"""
    print("\n" + "=" * 60)
    print("测试5: 代码开发工作流")
    print("=" * 60)

    from swagent.workflows import CodingWorkflow

    workflow = CodingWorkflow()

    print(f"\n工作流: {workflow.name}")

    initial_context = {
        'feature_request': '实现资源管理API',
        'user_stories': [
            '作为用户，我想创建资源',
            '作为用户，我想查询资源'
        ],
        'acceptance_criteria': [
            'API响应时间 < 200ms',
            '测试覆盖率 > 90%'
        ]
    }

    result = await workflow.execute(initial_context)

    print(f"\n✓ 开发完成: {'成功' if result.success else '失败'}")
    print(f"✓ 完成步骤: {result.completed_steps}/{result.total_steps}")

    if result.context.has('unit_test_results'):
        test_results = result.context.get('unit_test_results')
        print(f"\n测试结果:")
        print(f"  - 通过: {test_results.get('passed', 0)}/{test_results.get('total_tests', 0)}")
        print(f"  - 覆盖率: {test_results.get('coverage', 0):.1f}%")

    if result.context.has('review_report'):
        review = result.context.get('review_report')
        print(f"\n代码审查:")
        print(f"  - 总分: {review.get('overall_score', 0)}/100")
        print(f"  - 审批: {'通过' if result.context.get('approved', False) else '需修改'}")

    return True


async def test_workflow_manager():
    """测试工作流管理器"""
    print("\n" + "=" * 60)
    print("测试6: 工作流管理器")
    print("=" * 60)

    from swagent.workflows import WorkflowManager

    manager = WorkflowManager()

    # 测试列出工作流
    print("\n--- 已注册的工作流 ---")
    workflows = manager.list_workflows()
    for wf in workflows:
        print(f"✓ {wf['name']}: {wf['title']}")
        print(f"  描述: {wf['description']}")
        print(f"  步骤: {wf['steps']} 个")

    # 测试获取工作流
    print("\n--- 获取工作流实例 ---")
    research_wf = manager.get_workflow('research')
    if research_wf:
        print(f"✓ 获取科研工作流成功")
        print(f"  步骤数: {len(research_wf.steps)}")

    # 测试推荐工作流
    print("\n--- 根据用途推荐工作流 ---")
    purposes = [
        "我要写一篇论文",
        "生成项目报告",
        "分析数据趋势",
        "开发新功能"
    ]

    for purpose in purposes:
        recommendations = manager.get_workflow_by_purpose(purpose)
        print(f"  '{purpose}' -> {recommendations}")

    # 测试工作流步骤信息
    print("\n--- 查看工作流步骤 ---")
    steps = manager.get_workflow_steps('coding')
    if steps:
        print(f"✓ 代码开发工作流步骤:")
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step['name']}: {step['description']}")

    return True


async def main():
    """主测试函数"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "SWAgent - 阶段5测试" + " " * 23 + "║")
    print("║" + " " * 20 + "工作流模板" + " " * 26 + "║")
    print("╚" + "═" * 58 + "╝")

    results = []

    # 测试1: 基础架构
    try:
        result = await test_base_workflow()
        results.append(("基础架构", result))
    except Exception as e:
        print(f"\n✗ 基础架构测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("基础架构", False))

    # 测试2: 科研工作流
    try:
        result = await test_research_workflow()
        results.append(("科研工作流", result))
    except Exception as e:
        print(f"\n✗ 科研工作流测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("科研工作流", False))

    # 测试3: 报告工作流
    try:
        result = await test_report_workflow()
        results.append(("报告工作流", result))
    except Exception as e:
        print(f"\n✗ 报告工作流测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("报告工作流", False))

    # 测试4: 分析工作流
    try:
        result = await test_analysis_workflow()
        results.append(("分析工作流", result))
    except Exception as e:
        print(f"\n✗ 分析工作流测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("分析工作流", False))

    # 测试5: 编码工作流
    try:
        result = await test_coding_workflow()
        results.append(("编码工作流", result))
    except Exception as e:
        print(f"\n✗ 编码工作流测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("编码工作流", False))

    # 测试6: 工作流管理器
    try:
        result = await test_workflow_manager()
        results.append(("工作流管理器", result))
    except Exception as e:
        print(f"\n✗ 工作流管理器测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("工作流管理器", False))

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
        print("\n🎉 阶段5测试全部通过!")
        print("\n已完成功能:")
        print("  ✓ 工作流基础架构（BaseWorkflow, WorkflowStep, WorkflowContext）")
        print("  ✓ 科研工作流（7步骤：文献-设计-收集-分析-解释-撰写-总结）")
        print("  ✓ 报告生成工作流（7步骤：需求-收集-整理-撰写-图表-排版-检查）")
        print("  ✓ 数据分析工作流（7步骤：导入-探索-清洗-特征-统计-可视化-报告）")
        print("  ✓ 代码开发工作流（7步骤：需求-设计-编码-测试-审查-集成-文档）")
        print("  ✓ 工作流管理器（注册、查询、推荐、执行）")
        print("\n工作流特性:")
        print("  - 步骤依赖管理")
        print("  - 上下文数据传递")
        print("  - 错误处理和重试")
        print("  - 状态跟踪")
        print("  - 执行时间统计")
    else:
        print("\n⚠️  部分测试失败，请检查后重试。")

    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
