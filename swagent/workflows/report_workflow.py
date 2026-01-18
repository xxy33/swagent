"""
报告生成工作流
用于生成各类技术报告、评估报告、项目报告等
"""
from typing import Dict, Any
from .base_workflow import BaseWorkflow, WorkflowContext


class ReportWorkflow(BaseWorkflow):
    """
    报告生成工作流模板

    步骤：
    1. 需求分析 - 明确报告类型和要求
    2. 数据收集 - 收集报告所需数据和信息
    3. 数据整理 - 整理和组织数据
    4. 内容撰写 - 撰写报告各部分内容
    5. 图表生成 - 生成可视化图表
    6. 格式排版 - 格式化和排版报告
    7. 质量检查 - 检查报告完整性和准确性
    """

    def __init__(self):
        super().__init__(
            name="报告生成工作流",
            description="支持技术报告、评估报告、项目报告等的自动化生成"
        )

    def _setup_steps(self):
        """设置报告生成工作流的具体步骤"""

        # 步骤1: 需求分析
        self.add_step(
            name="requirement_analysis",
            description="明确报告类型、目标受众和格式要求",
            execute_func=self._requirement_analysis,
            required_inputs=["report_type", "report_purpose"],
            optional_inputs=["target_audience", "template"],
            outputs=["report_outline", "content_requirements"]
        )

        # 步骤2: 数据收集
        self.add_step(
            name="data_collection",
            description="收集报告所需的数据、资料和信息",
            execute_func=self._data_collection,
            required_inputs=["content_requirements"],
            optional_inputs=["data_sources", "time_period"],
            outputs=["collected_data", "data_inventory"]
        )

        # 步骤3: 数据整理
        self.add_step(
            name="data_organization",
            description="整理、分类和汇总数据",
            execute_func=self._data_organization,
            required_inputs=["collected_data"],
            optional_inputs=["organization_method"],
            outputs=["organized_data", "summary_statistics"]
        )

        # 步骤4: 内容撰写
        self.add_step(
            name="content_writing",
            description="撰写报告的各个部分",
            execute_func=self._content_writing,
            required_inputs=["report_outline", "organized_data"],
            optional_inputs=["writing_style"],
            outputs=["report_sections", "executive_summary"]
        )

        # 步骤5: 图表生成
        self.add_step(
            name="chart_generation",
            description="生成数据可视化图表",
            execute_func=self._chart_generation,
            required_inputs=["organized_data"],
            optional_inputs=["chart_types", "color_scheme"],
            outputs=["charts", "chart_descriptions"]
        )

        # 步骤6: 格式排版
        self.add_step(
            name="formatting",
            description="格式化和排版报告",
            execute_func=self._formatting,
            required_inputs=["report_sections", "charts"],
            optional_inputs=["template", "style_guide"],
            outputs=["formatted_report", "table_of_contents"]
        )

        # 步骤7: 质量检查
        self.add_step(
            name="quality_check",
            description="检查报告的完整性、准确性和一致性",
            execute_func=self._quality_check,
            required_inputs=["formatted_report"],
            optional_inputs=["checklist"],
            outputs=["final_report", "quality_report", "recommendations"]
        )

    async def _requirement_analysis(self, context: WorkflowContext) -> Dict[str, Any]:
        """执行需求分析步骤"""
        report_type = context.get('report_type')
        report_purpose = context.get('report_purpose')
        target_audience = context.get('target_audience', '管理层')
        template = context.get('template', 'standard')

        # 根据报告类型生成大纲
        report_outlines = {
            'technical': ['执行摘要', '技术背景', '方法论', '结果分析', '结论与建议', '参考文献'],
            'assessment': ['执行摘要', '评估目标', '评估方法', '现状分析', '问题识别', '改进建议', '实施计划'],
            'project': ['项目概述', '进度报告', '预算执行', '风险分析', '下阶段计划', '附录'],
            'annual': ['公司概况', '年度亮点', '财务表现', '业务分析', '风险与挑战', '未来展望']
        }

        report_outline = report_outlines.get(report_type, report_outlines['technical'])

        content_requirements = {
            'sections': report_outline,
            'length': '15-20页' if template == 'detailed' else '8-12页',
            'style': '正式、客观' if target_audience == '管理层' else '技术性、详细',
            'visuals': '每部分至少1个图表',
            'references': '是' if report_type in ['technical', 'assessment'] else '否'
        }

        return {
            'report_outline': report_outline,
            'content_requirements': content_requirements,
            'report_structure': f"报告将包含{len(report_outline)}个主要部分"
        }

    async def _data_collection(self, context: WorkflowContext) -> Dict[str, Any]:
        """执行数据收集步骤"""
        content_reqs = context.get('content_requirements')
        data_sources = context.get('data_sources', ['database', 'surveys', 'literature'])
        time_period = context.get('time_period', '2024年度')

        # 模拟数据收集
        collected_data = {
            'quantitative': {
                'waste_volume': [120, 135, 142, 138, 145],
                'recycling_rate': [45, 48, 52, 54, 56],
                'cost': [2.5, 2.7, 2.8, 2.9, 3.0]
            },
            'qualitative': {
                'stakeholder_feedback': ['positive', 'concerns about cost', 'supportive'],
                'challenges': ['budget constraints', 'technical limitations'],
                'opportunities': ['new technologies', 'policy support']
            },
            'metadata': {
                'collection_period': time_period,
                'sources': data_sources,
                'completeness': '92%'
            }
        }

        data_inventory = f"""
## 数据清单

### 定量数据
- 废物处理量：5个数据点
- 回收率：5个数据点
- 成本数据：5个数据点

### 定性数据
- 利益相关者反馈：3条
- 挑战识别：2项
- 机遇分析：2项

### 元数据
- 数据时段：{time_period}
- 数据来源：{', '.join(data_sources)}
- 数据完整性：92%
"""

        return {
            'collected_data': collected_data,
            'data_inventory': data_inventory
        }

    async def _data_organization(self, context: WorkflowContext) -> Dict[str, Any]:
        """执行数据整理步骤"""
        collected_data = context.get('collected_data')
        org_method = context.get('organization_method', 'by_topic')

        # 整理数据
        organized_data = {
            'performance_metrics': {
                'waste_processing': {
                    'average': 136,
                    'trend': 'increasing',
                    'growth_rate': '20.8%'
                },
                'recycling': {
                    'average_rate': 51,
                    'improvement': '+11%'
                },
                'cost_efficiency': {
                    'average_cost': 2.78,
                    'unit': 'million CNY',
                    'trend': 'stable'
                }
            },
            'key_insights': [
                "废物处理量稳步增长",
                "回收率显著提升",
                "成本保持稳定"
            ],
            'data_tables': {
                'monthly_performance': 'table_1.csv',
                'cost_breakdown': 'table_2.csv'
            }
        }

        summary_statistics = """
## 数据摘要统计

### 绩效指标
- 平均处理量：136吨/日 (↑20.8%)
- 平均回收率：51% (↑11%)
- 平均成本：2.78百万元 (稳定)

### 关键洞察
1. 废物处理量稳步增长，反映业务扩张
2. 回收率显著提升，达到行业领先水平
3. 成本控制良好，保持稳定
"""

        return {
            'organized_data': organized_data,
            'summary_statistics': summary_statistics
        }

    async def _content_writing(self, context: WorkflowContext) -> Dict[str, Any]:
        """执行内容撰写步骤"""
        report_outline = context.get('report_outline')
        organized_data = context.get('organized_data')
        writing_style = context.get('writing_style', 'formal')

        # 撰写各部分内容
        executive_summary = """
# 执行摘要

本报告总结了2024年度固体废物管理项目的执行情况。主要发现包括：

**业绩亮点：**
- 废物处理量增长20.8%，达到136吨/日
- 回收率提升11个百分点，达到51%
- 成本控制良好，保持在预算范围内

**主要挑战：**
- 预算约束限制了扩建计划
- 部分技术设备需要升级

**建议：**
- 申请额外预算支持技术升级
- 加强利益相关者沟通
- 探索新技术应用机会
"""

        report_sections = {}
        for section in report_outline:
            if section == '执行摘要':
                report_sections[section] = executive_summary
            else:
                report_sections[section] = f"# {section}\n\n[{section}的详细内容]\n\n"

        return {
            'report_sections': report_sections,
            'executive_summary': executive_summary,
            'word_count': 3500
        }

    async def _chart_generation(self, context: WorkflowContext) -> Dict[str, Any]:
        """执行图表生成步骤"""
        organized_data = context.get('organized_data')
        chart_types = context.get('chart_types', ['line', 'bar', 'pie'])
        color_scheme = context.get('color_scheme', 'professional')

        # 生成图表配置
        charts = [
            {
                'id': 'chart_1',
                'type': 'line',
                'title': '废物处理量趋势',
                'data': 'waste_volume_time_series',
                'file': 'chart_1_waste_trend.png'
            },
            {
                'id': 'chart_2',
                'type': 'bar',
                'title': '回收率对比',
                'data': 'recycling_rate_comparison',
                'file': 'chart_2_recycling.png'
            },
            {
                'id': 'chart_3',
                'type': 'pie',
                'title': '成本构成',
                'data': 'cost_breakdown',
                'file': 'chart_3_cost.png'
            }
        ]

        chart_descriptions = {
            'chart_1': '图1显示了过去5个月的废物处理量呈现稳步上升趋势',
            'chart_2': '图2对比了不同月份的回收率，显示持续改善',
            'chart_3': '图3展示了成本的主要构成部分'
        }

        return {
            'charts': charts,
            'chart_descriptions': chart_descriptions,
            'chart_count': len(charts)
        }

    async def _formatting(self, context: WorkflowContext) -> Dict[str, Any]:
        """执行格式排版步骤"""
        report_sections = context.get('report_sections')
        charts = context.get('charts')
        template = context.get('template', 'standard')
        style_guide = context.get('style_guide', 'corporate')

        # 生成目录
        table_of_contents = "# 目录\n\n"
        for i, section in enumerate(report_sections.keys(), 1):
            table_of_contents += f"{i}. {section} ........... {i}\n"

        # 组装完整报告
        formatted_report = f"""
# 固体废物管理年度报告

{table_of_contents}

---

{''.join(report_sections.values())}

---

## 图表索引

"""
        for chart in charts:
            formatted_report += f"- 图{chart['id'][-1]}: {chart['title']}\n"

        return {
            'formatted_report': formatted_report,
            'table_of_contents': table_of_contents,
            'page_count': 18,
            'format': 'PDF + DOCX'
        }

    async def _quality_check(self, context: WorkflowContext) -> Dict[str, Any]:
        """执行质量检查步骤"""
        formatted_report = context.get('formatted_report')
        checklist = context.get('checklist', [
            '完整性', '准确性', '一致性', '格式规范', '图表质量'
        ])

        # 质量检查结果
        quality_report = {
            '完整性': {'status': 'pass', 'score': 100, 'note': '所有章节完整'},
            '准确性': {'status': 'pass', 'score': 98, 'note': '数据准确，来源可靠'},
            '一致性': {'status': 'pass', 'score': 95, 'note': '术语和格式一致'},
            '格式规范': {'status': 'pass', 'score': 100, 'note': '符合企业标准'},
            '图表质量': {'status': 'pass', 'score': 95, 'note': '图表清晰美观'}
        }

        overall_score = sum(item['score'] for item in quality_report.values()) / len(quality_report)

        recommendations = []
        if overall_score < 100:
            recommendations.append("建议在最终提交前进行人工校对")

        final_report = {
            'content': formatted_report,
            'quality_score': overall_score,
            'status': 'approved' if overall_score >= 90 else 'needs_revision',
            'file_formats': ['PDF', 'DOCX', 'HTML']
        }

        return {
            'final_report': final_report,
            'quality_report': quality_report,
            'recommendations': recommendations,
            'overall_quality_score': overall_score
        }
