"""
长文报告生成示例
演示如何使用工作流系统生成专业的长篇报告
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from swagent.workflows import ReportWorkflow, ResearchWorkflow, BaseWorkflow, WorkflowContext
from swagent.agents import ReActAgent
from swagent.tools.domain import EmissionCalculator, Visualizer
from swagent.llm import OpenAIClient, LLMConfig


async def generate_technical_report():
    """
    示例1: 生成技术评估报告
    场景: 评估某垃圾处理技术的应用效果
    """
    print("\n" + "=" * 80)
    print("示例1: 生成技术评估报告")
    print("=" * 80)

    # 创建报告工作流
    report_workflow = ReportWorkflow()

    # 准备初始数据
    initial_context = {
        # 报告基本信息
        "report_type": "technical",
        "report_purpose": "评估X市垃圾焚烧发电厂2024年运行效果",
        "target_audience": "管理层和技术团队",
        "template": "detailed",

        # 数据来源
        "data_sources": [
            "运营数据库",
            "环境监测系统",
            "财务系统",
            "用户反馈问卷"
        ],
        "time_period": "2024年1月-12月",

        # 格式要求
        "writing_style": "formal",
        "chart_types": ["line", "bar", "pie", "scatter"],
        "color_scheme": "professional",

        # 质量标准
        "checklist": [
            "数据完整性",
            "分析准确性",
            "格式规范性",
            "逻辑连贯性",
            "图表清晰度"
        ]
    }

    # 执行工作流
    print("\n开始生成技术评估报告...")
    print("-" * 80)

    result = await report_workflow.execute(
        initial_context=initial_context,
        stop_on_error=False
    )

    # 输出执行结果
    print(f"\n工作流执行完成!")
    print(f"成功: {result.success}")
    print(f"完成率: {result.completion_rate * 100:.1f}%")
    print(f"总耗时: {result.duration:.2f}秒")
    print(f"\n步骤执行情况:")
    print("-" * 80)

    for step_result in result.step_results:
        status_icon = "✓" if step_result['status'] == 'completed' else "✗"
        print(f"{status_icon} {step_result['name']}: {step_result['status']}")
        if step_result['duration']:
            print(f"   耗时: {step_result['duration']:.2f}秒")

    # 获取最终报告
    if result.success:
        final_report = result.context.get('final_report')

        print("\n" + "=" * 80)
        print("报告质量评估")
        print("=" * 80)
        print(f"质量评分: {final_report['quality_score']:.1f}/100")
        print(f"审批状态: {final_report['status']}")
        print(f"输出格式: {', '.join(final_report['file_formats'])}")

        # 保存报告
        report_content = final_report['content']
        output_file = "technical_assessment_report_2024.md"

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        print(f"\n✓ 报告已保存到: {output_file}")

        # 显示报告摘要
        executive_summary = result.context.get('executive_summary')
        print("\n" + "=" * 80)
        print("执行摘要预览")
        print("=" * 80)
        print(executive_summary[:500] + "...")

    else:
        print(f"\n✗ 报告生成失败: {result.error}")

    return result


async def generate_research_report():
    """
    示例2: 生成科研报告
    场景: 固体废物厌氧消化技术研究
    """
    print("\n\n" + "=" * 80)
    print("示例2: 生成科研报告")
    print("=" * 80)

    # 创建科研工作流
    research_workflow = ResearchWorkflow()

    # 准备研究参数
    research_context = {
        # 研究主题
        "research_topic": "有机固体废物厌氧消化技术优化研究",

        # 关键词
        "keywords": [
            "厌氧消化",
            "有机废物",
            "沼气产量",
            "微生物群落",
            "工艺优化"
        ],

        # 文献检索参数
        "time_range": "2020-2024",
        "literature_sources": [
            "Web of Science",
            "Google Scholar",
            "PubMed",
            "中国知网"
        ],

        # 研究方法偏好
        "methodology_preference": "mixed",

        # 数据来源
        "data_sources": [
            "field_survey",
            "laboratory",
            "literature"
        ],

        # 分析工具
        "analysis_tools": ["Python", "SPSS", "R"],

        # 目标期刊
        "target_journal": "Bioresource Technology",
        "citation_style": "APA",

        # 统计显著性水平
        "significance_level": 0.05
    }

    # 执行研究工作流
    print("\n开始执行科研工作流...")
    print("-" * 80)

    result = await research_workflow.execute(
        initial_context=research_context
    )

    # 输出结果
    print(f"\n科研工作流执行完成!")
    print(f"完成率: {result.completion_rate * 100:.1f}%")
    print(f"总耗时: {result.duration:.2f}秒")

    # 获取关键输出
    if result.success:
        # 文献综述
        literature_summary = result.context.get('literature_summary')
        print("\n" + "=" * 80)
        print("文献综述预览")
        print("=" * 80)
        print(literature_summary[:400] + "...")

        # 研究发现
        findings = result.context.get('findings')
        print("\n" + "=" * 80)
        print("研究发现预览")
        print("=" * 80)
        print(findings[:400] + "...")

        # 论文草稿
        paper_draft = result.context.get('paper_draft')

        # 保存论文
        with open("research_paper_draft.md", 'w', encoding='utf-8') as f:
            f.write(paper_draft)

        print("\n✓ 论文草稿已保存到: research_paper_draft.md")

        # 最终结论
        final_conclusions = result.context.get('final_conclusions')
        print("\n" + "=" * 80)
        print("研究总结预览")
        print("=" * 80)
        print(final_conclusions[:400] + "...")

    return result


async def custom_report_workflow():
    """
    示例3: 自定义报告工作流
    场景: 企业环保绩效报告(集成AI分析)
    """
    print("\n\n" + "=" * 80)
    print("示例3: 自定义企业环保绩效报告")
    print("=" * 80)

    class CustomEnterpriseReport(BaseWorkflow):
        """自定义企业报告工作流"""

        def __init__(self):
            super().__init__(
                name="企业环保绩效报告",
                description="生成包含数据分析和AI洞察的企业环保报告"
            )
            self.analyst_agent = None
            self.emission_calc = EmissionCalculator()
            self.visualizer = Visualizer()

        def _setup_steps(self):
            """定义工作流步骤"""

            # 步骤1: 数据采集
            self.add_step(
                name="data_collection",
                description="采集运营数据和环保数据",
                execute_func=self._collect_enterprise_data,
                required_inputs=["company_id", "year"],
                outputs=["raw_data", "data_summary"]
            )

            # 步骤2: 排放计算
            self.add_step(
                name="emission_calculation",
                description="计算碳排放和环境影响",
                execute_func=self._calculate_emissions,
                required_inputs=["raw_data"],
                outputs=["emission_data", "reduction_potential"]
            )

            # 步骤3: AI分析
            self.add_step(
                name="ai_analysis",
                description="使用AI Agent进行深度分析",
                execute_func=self._ai_deep_analysis,
                required_inputs=["emission_data", "raw_data"],
                outputs=["ai_insights", "recommendations"]
            )

            # 步骤4: 可视化
            self.add_step(
                name="visualization",
                description="生成专业图表",
                execute_func=self._generate_visualizations,
                required_inputs=["emission_data"],
                outputs=["charts", "infographics"]
            )

            # 步骤5: 报告撰写
            self.add_step(
                name="report_writing",
                description="生成完整报告",
                execute_func=self._write_final_report,
                required_inputs=["ai_insights", "charts", "recommendations"],
                outputs=["final_report"]
            )

        async def _collect_enterprise_data(self, context: WorkflowContext):
            """采集企业数据"""
            company_id = context.get('company_id')
            year = context.get('year')

            # 模拟数据采集
            raw_data = {
                "waste_generated": 15000,
                "waste_treated": {
                    "recycling": 7500,
                    "composting": 3000,
                    "incineration": 3500,
                    "landfill": 1000
                },
                "energy_consumed": 2500000,
                "water_usage": 50000,
                "costs": {
                    "treatment": 4500000,
                    "disposal": 800000,
                    "equipment": 1200000
                }
            }

            print(f"  ✓ 数据采集完成: {company_id} {year}年度")

            return {
                "raw_data": raw_data,
                "data_summary": f"{company_id}公司{year}年度环保数据采集完成"
            }

        async def _calculate_emissions(self, context: WorkflowContext):
            """计算排放"""
            raw_data = context.get('raw_data')

            total_emissions = 0
            detailed_emissions = {}

            for method, quantity in raw_data['waste_treated'].items():
                result = await self.emission_calc.execute(
                    waste_type="mixed",
                    treatment_method=method,
                    quantity=quantity
                )
                emissions = result.data['total_emission_kgCO2e']
                detailed_emissions[method] = emissions
                total_emissions += emissions

            reduction_potential = {
                "current_emissions": total_emissions,
                "optimal_emissions": total_emissions * 0.6,
                "reduction_potential": total_emissions * 0.4
            }

            print(f"  ✓ 排放计算完成: 总排放 {total_emissions:.0f} kg CO2e")

            return {
                "emission_data": {
                    "total": total_emissions,
                    "by_method": detailed_emissions
                },
                "reduction_potential": reduction_potential
            }

        async def _ai_deep_analysis(self, context: WorkflowContext):
            """AI深度分析"""
            emission_data = context.get('emission_data')
            raw_data = context.get('raw_data')

            # 创建分析Agent
            if not self.analyst_agent:
                from swagent.core.base_agent import AgentConfig
                llm_config = LLMConfig(provider="openai", model="gpt-4")
                llm = OpenAIClient(llm_config)

                analyst_config = AgentConfig(
                    name="环保分析师",
                    role="数据分析专家"
                )
                self.analyst_agent = ReActAgent(analyst_config)
                self.analyst_agent.llm = llm

            # 构建分析提示
            analysis_prompt = f"""
            请分析以下企业环保数据:

            废物处理情况:
            - 总产生量: {raw_data['waste_generated']}吨/年
            - 回收: {raw_data['waste_treated']['recycling']}吨
            - 堆肥: {raw_data['waste_treated']['composting']}吨
            - 焚烧: {raw_data['waste_treated']['incineration']}吨
            - 填埋: {raw_data['waste_treated']['landfill']}吨

            碳排放:
            - 总排放: {emission_data['total']:.0f} kg CO2e

            请提供:
            1. 数据的关键洞察(3-5条)
            2. 存在的问题和风险
            3. 改进建议(具体可行)
            4. 行业对标分析
            """

            ai_response = await self.analyst_agent.chat(analysis_prompt)

            print(f"  ✓ AI分析完成")

            return {
                "ai_insights": ai_response,
                "recommendations": [
                    "提高回收率至60%以上",
                    "减少填埋比例至5%以下",
                    "优化处理工艺降低能耗",
                    "建立实时监控系统"
                ]
            }

        async def _generate_visualizations(self, context: WorkflowContext):
            """生成可视化"""
            emission_data = context.get('emission_data')

            chart1_result = await self.visualizer.execute(
                chart_type="pie",
                data={
                    "labels": list(emission_data['by_method'].keys()),
                    "values": list(emission_data['by_method'].values())
                },
                title="各处理方式碳排放分布"
            )

            print(f"  ✓ 图表生成完成")

            return {
                "charts": [chart1_result.data],
                "infographics": ["emissions_comparison.png"]
            }

        async def _write_final_report(self, context: WorkflowContext):
            """撰写最终报告"""
            ai_insights = context.get('ai_insights')
            recommendations = context.get('recommendations')
            emission_data = context.get('emission_data')

            report_content = f"""
# 企业环保绩效年度报告

## 执行摘要

本报告全面评估了我司2024年度环保绩效，通过AI智能分析系统深度挖掘数据价值。

### 关键指标
- 废物总处理量: 15,000吨
- 总碳排放: {emission_data['total']:.0f} kg CO2e
- 回收率: 50%

## AI智能分析

{ai_insights}

## 改进建议

{"".join([f"{i+1}. {rec}\n" for i, rec in enumerate(recommendations)])}

## 图表附录

[图表内容]

---
报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
由SWAgent智能系统自动生成
            """

            print(f"  ✓ 报告撰写完成")

            return {
                "final_report": report_content
            }

    # 使用自定义工作流
    print("\n开始执行自定义工作流...")
    print("-" * 80)

    custom_workflow = CustomEnterpriseReport()

    result = await custom_workflow.execute(
        initial_context={
            "company_id": "ABC集团",
            "year": 2024
        }
    )

    if result.success:
        final_report = result.context.get('final_report')

        # 保存报告
        with open("enterprise_report_2024.md", 'w', encoding='utf-8') as f:
            f.write(final_report)

        print("\n" + "=" * 80)
        print("报告预览")
        print("=" * 80)
        print(final_report[:600] + "...")

        print("\n✓ 自定义报告已保存到: enterprise_report_2024.md")

    return result


async def main():
    """主函数"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 24 + "长文报告生成示例" + " " * 32 + "║")
    print("╚" + "═" * 78 + "╝")

    # 示例1: 技术评估报告
    await generate_technical_report()

    # 示例2: 科研报告
    await generate_research_report()

    # 示例3: 自定义报告
    await custom_report_workflow()

    print("\n\n" + "=" * 80)
    print("✓ 所有示例运行完成")
    print("=" * 80)
    print("\n核心功能:")
    print("  1. 结构化内容生成 - 自动组织章节结构")
    print("  2. 数据整合分析 - 整合多源数据并分析")
    print("  3. 专业图表生成 - 自动生成可视化图表")
    print("  4. 质量控制 - 多维度质量检查")
    print("  5. 自定义工作流 - 灵活扩展满足特定需求")
    print()


if __name__ == "__main__":
    asyncio.run(main())
