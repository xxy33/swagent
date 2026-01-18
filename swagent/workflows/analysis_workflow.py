"""
数据分析工作流
用于数据探索、清洗、分析和可视化
"""
from typing import Dict, Any
from .base_workflow import BaseWorkflow, WorkflowContext


class DataAnalysisWorkflow(BaseWorkflow):
    """
    数据分析工作流模板

    步骤：
    1. 数据导入 - 加载和导入数据
    2. 数据探索 - 初步探索数据特征
    3. 数据清洗 - 处理缺失值和异常值
    4. 特征工程 - 创建和选择特征
    5. 统计分析 - 进行统计分析
    6. 可视化 - 生成数据可视化
    7. 报告生成 - 生成分析报告
    """

    def __init__(self):
        super().__init__(
            name="数据分析工作流",
            description="支持数据探索、清洗、分析和可视化的完整流程"
        )

    def _setup_steps(self):
        """设置数据分析工作流的具体步骤"""

        # 步骤1: 数据导入
        self.add_step(
            name="data_import",
            description="从各种来源加载数据",
            execute_func=self._data_import,
            required_inputs=["data_source"],
            optional_inputs=["file_format", "connection_params"],
            outputs=["raw_dataframe", "data_info"]
        )

        # 步骤2: 数据探索
        self.add_step(
            name="data_exploration",
            description="探索数据的基本特征和分布",
            execute_func=self._data_exploration,
            required_inputs=["raw_dataframe"],
            optional_inputs=["exploration_depth"],
            outputs=["basic_stats", "data_profile", "initial_insights"]
        )

        # 步骤3: 数据清洗
        self.add_step(
            name="data_cleaning",
            description="处理缺失值、异常值和重复数据",
            execute_func=self._data_cleaning,
            required_inputs=["raw_dataframe", "data_profile"],
            optional_inputs=["cleaning_strategy"],
            outputs=["clean_dataframe", "cleaning_report"]
        )

        # 步骤4: 特征工程
        self.add_step(
            name="feature_engineering",
            description="创建新特征和选择重要特征",
            execute_func=self._feature_engineering,
            required_inputs=["clean_dataframe"],
            optional_inputs=["feature_methods"],
            outputs=["engineered_dataframe", "feature_importance"]
        )

        # 步骤5: 统计分析
        self.add_step(
            name="statistical_analysis",
            description="进行描述性和推断性统计分析",
            execute_func=self._statistical_analysis,
            required_inputs=["engineered_dataframe"],
            optional_inputs=["analysis_methods"],
            outputs=["statistics", "correlations", "test_results"]
        )

        # 步骤6: 可视化
        self.add_step(
            name="visualization",
            description="生成数据可视化图表",
            execute_func=self._visualization,
            required_inputs=["engineered_dataframe", "statistics"],
            optional_inputs=["chart_types"],
            outputs=["visualizations", "viz_descriptions"]
        )

        # 步骤7: 报告生成
        self.add_step(
            name="report_generation",
            description="生成数据分析报告",
            execute_func=self._report_generation,
            required_inputs=["statistics", "visualizations"],
            optional_inputs=["report_template"],
            outputs=["analysis_report", "key_findings"]
        )

    async def _data_import(self, context: WorkflowContext) -> Dict[str, Any]:
        """执行数据导入步骤"""
        data_source = context.get('data_source')
        file_format = context.get('file_format', 'csv')
        conn_params = context.get('connection_params', {})

        # 模拟数据导入
        raw_dataframe = {
            'shape': (1000, 15),
            'columns': [
                'id', 'date', 'waste_type', 'quantity', 'treatment_method',
                'cost', 'emission', 'recycling_rate', 'location', 'operator',
                'temperature', 'moisture', 'composition_a', 'composition_b', 'composition_c'
            ],
            'dtypes': {
                'numeric': 8,
                'categorical': 5,
                'datetime': 1,
                'text': 1
            }
        }

        data_info = f"""
## 数据导入信息

### 数据来源
- 来源：{data_source}
- 格式：{file_format}
- 导入时间：2024-01-17 14:30:00

### 数据规模
- 行数：{raw_dataframe['shape'][0]}
- 列数：{raw_dataframe['shape'][1]}
- 内存占用：约 1.2 MB

### 列信息
- 数值型：{raw_dataframe['dtypes']['numeric']} 列
- 分类型：{raw_dataframe['dtypes']['categorical']} 列
- 日期型：{raw_dataframe['dtypes']['datetime']} 列
- 文本型：{raw_dataframe['dtypes']['text']} 列
"""

        return {
            'raw_dataframe': raw_dataframe,
            'data_info': data_info,
            'import_status': 'success'
        }

    async def _data_exploration(self, context: WorkflowContext) -> Dict[str, Any]:
        """执行数据探索步骤"""
        raw_df = context.get('raw_dataframe')
        depth = context.get('exploration_depth', 'standard')

        # 基本统计
        basic_stats = {
            'quantity': {
                'mean': 125.3,
                'median': 118.5,
                'std': 34.7,
                'min': 45.0,
                'max': 285.0
            },
            'cost': {
                'mean': 2850.5,
                'median': 2720.0,
                'std': 680.2,
                'min': 1200.0,
                'max': 5400.0
            },
            'emission': {
                'mean': 420.8,
                'median': 395.0,
                'std': 125.3,
                'min': 150.0,
                'max': 850.0
            }
        }

        data_profile = {
            'missing_values': {
                'total': 45,
                'columns': {
                    'moisture': 15,
                    'composition_c': 30
                }
            },
            'duplicates': 3,
            'outliers': {
                'quantity': 12,
                'cost': 8,
                'emission': 10
            },
            'skewness': {
                'quantity': 0.32,
                'cost': 0.45,
                'emission': 0.28
            }
        }

        initial_insights = [
            "数据分布较为对称，偏度较小",
            "缺失值集中在moisture和composition_c列",
            "存在少量异常值需要处理",
            "重复记录较少"
        ]

        return {
            'basic_stats': basic_stats,
            'data_profile': data_profile,
            'initial_insights': initial_insights
        }

    async def _data_cleaning(self, context: WorkflowContext) -> Dict[str, Any]:
        """执行数据清洗步骤"""
        raw_df = context.get('raw_dataframe')
        profile = context.get('data_profile')
        strategy = context.get('cleaning_strategy', 'conservative')

        # 数据清洗操作
        cleaning_actions = {
            'missing_values': {
                'method': 'median_imputation',
                'affected_rows': profile['missing_values']['total']
            },
            'duplicates': {
                'removed': profile['duplicates']
            },
            'outliers': {
                'method': 'IQR',
                'handled': 30,
                'action': 'cap' if strategy == 'conservative' else 'remove'
            },
            'normalization': {
                'applied': True,
                'method': 'min-max'
            }
        }

        clean_dataframe = {
            'shape': (997, 15),  # 删除了3个重复行
            'columns': raw_df['columns'],
            'quality_score': 95.5
        }

        cleaning_report = f"""
## 数据清洗报告

### 缺失值处理
- 方法：中位数填充
- 处理行数：{cleaning_actions['missing_values']['affected_rows']}

### 重复值处理
- 删除重复行：{cleaning_actions['duplicates']['removed']}

### 异常值处理
- 检测方法：{cleaning_actions['outliers']['method']}
- 处理数量：{cleaning_actions['outliers']['handled']}
- 处理策略：{cleaning_actions['outliers']['action']}

### 数据规范化
- 应用：{cleaning_actions['normalization']['applied']}
- 方法：{cleaning_actions['normalization']['method']}

### 清洗后数据质量
- 质量评分：{clean_dataframe['quality_score']}/100
- 最终行数：{clean_dataframe['shape'][0]}
"""

        return {
            'clean_dataframe': clean_dataframe,
            'cleaning_report': cleaning_report,
            'quality_improvement': 15.5
        }

    async def _feature_engineering(self, context: WorkflowContext) -> Dict[str, Any]:
        """执行特征工程步骤"""
        clean_df = context.get('clean_dataframe')
        methods = context.get('feature_methods', ['derived', 'interaction'])

        # 特征工程
        new_features = [
            'cost_per_ton',  # 成本/数量
            'emission_per_ton',  # 排放/数量
            'efficiency_score',  # 综合效率指标
            'season',  # 从日期提取季节
            'is_weekend'  # 是否周末
        ]

        engineered_dataframe = {
            'shape': (997, 20),  # 增加了5个特征
            'new_features': new_features,
            'total_features': clean_df['shape'][1] + len(new_features)
        }

        feature_importance = {
            'cost_per_ton': 0.28,
            'emission_per_ton': 0.25,
            'quantity': 0.18,
            'recycling_rate': 0.15,
            'efficiency_score': 0.14
        }

        return {
            'engineered_dataframe': engineered_dataframe,
            'feature_importance': feature_importance,
            'new_feature_count': len(new_features)
        }

    async def _statistical_analysis(self, context: WorkflowContext) -> Dict[str, Any]:
        """执行统计分析步骤"""
        eng_df = context.get('engineered_dataframe')
        methods = context.get('analysis_methods', ['descriptive', 'correlation', 'hypothesis'])

        # 统计分析结果
        statistics = {
            'descriptive': {
                'cost_per_ton': {'mean': 22.8, 'std': 5.6},
                'emission_per_ton': {'mean': 3.36, 'std': 1.02},
                'recycling_rate': {'mean': 0.48, 'std': 0.15}
            },
            'distribution': {
                'cost_per_ton': 'normal',
                'emission_per_ton': 'slightly_right_skewed',
                'recycling_rate': 'uniform'
            }
        }

        correlations = {
            'cost_emission': {'r': 0.65, 'p': 0.001, 'significance': 'high'},
            'quantity_cost': {'r': 0.82, 'p': 0.0001, 'significance': 'very_high'},
            'recycling_emission': {'r': -0.58, 'p': 0.005, 'significance': 'moderate'}
        }

        test_results = {
            'anova': {
                'test': 'treatment_method vs emission',
                'f_statistic': 15.3,
                'p_value': 0.0001,
                'conclusion': '不同处理方法的排放存在显著差异'
            },
            't_test': {
                'test': 'recycling vs non-recycling emission',
                't_statistic': -8.5,
                'p_value': 0.0001,
                'conclusion': '回收显著降低排放'
            }
        }

        return {
            'statistics': statistics,
            'correlations': correlations,
            'test_results': test_results
        }

    async def _visualization(self, context: WorkflowContext) -> Dict[str, Any]:
        """执行可视化步骤"""
        eng_df = context.get('engineered_dataframe')
        stats = context.get('statistics')
        chart_types = context.get('chart_types', ['histogram', 'scatter', 'box', 'heatmap'])

        visualizations = [
            {
                'id': 'viz_1',
                'type': 'histogram',
                'title': '成本分布直方图',
                'variables': ['cost_per_ton'],
                'file': 'hist_cost.png'
            },
            {
                'id': 'viz_2',
                'type': 'scatter',
                'title': '数量 vs 成本散点图',
                'variables': ['quantity', 'cost'],
                'file': 'scatter_qty_cost.png'
            },
            {
                'id': 'viz_3',
                'type': 'box',
                'title': '各处理方法的排放对比',
                'variables': ['treatment_method', 'emission'],
                'file': 'box_treatment_emission.png'
            },
            {
                'id': 'viz_4',
                'type': 'heatmap',
                'title': '变量相关性热图',
                'variables': 'all_numeric',
                'file': 'heatmap_correlation.png'
            }
        ]

        viz_descriptions = {
            'viz_1': '成本呈现正态分布，集中在20-25元/吨',
            'viz_2': '数量与成本呈现强线性正相关（r=0.82）',
            'viz_3': '回收处理的排放明显低于填埋和焚烧',
            'viz_4': '强相关变量对包括：数量-成本、回收率-排放'
        }

        return {
            'visualizations': visualizations,
            'viz_descriptions': viz_descriptions,
            'chart_count': len(visualizations)
        }

    async def _report_generation(self, context: WorkflowContext) -> Dict[str, Any]:
        """执行报告生成步骤"""
        stats = context.get('statistics')
        viz = context.get('visualizations')
        template = context.get('report_template', 'standard')

        analysis_report = f"""
# 数据分析报告

## 执行摘要
本次分析处理了997条废物管理记录，进行了全面的数据探索、清洗和统计分析。

## 1. 数据概述
- 数据量：997条记录，20个特征
- 数据质量：95.5分
- 分析周期：2024年全年

## 2. 主要发现

### 2.1 描述性统计
- 平均单位成本：22.8 ± 5.6 元/吨
- 平均单位排放：3.36 ± 1.02 kg CO2e/吨
- 平均回收率：48% ± 15%

### 2.2 相关性分析
- 数量与成本高度正相关（r=0.82, p<0.0001）
- 回收率与排放负相关（r=-0.58, p<0.005）
- 成本与排放正相关（r=0.65, p<0.001）

### 2.3 假设检验
- 不同处理方法的排放存在显著差异（F=15.3, p<0.0001）
- 回收处理显著降低排放（t=-8.5, p<0.0001）

## 3. 可视化
共生成{len(viz)}个可视化图表，详见附图。

## 4. 结论与建议
1. 优先推广回收处理，可显著降低排放
2. 优化处理规模以提高成本效益
3. 建立回收率与排放的监控机制

## 5. 附录
- 数据质量报告
- 详细统计表
- 可视化图表
"""

        key_findings = [
            "数量与成本呈强正相关（r=0.82）",
            "回收处理可降低58%的排放",
            "不同处理方法的环境影响差异显著",
            "平均回收率达到48%，仍有提升空间"
        ]

        return {
            'analysis_report': analysis_report,
            'key_findings': key_findings,
            'report_format': 'markdown + PDF'
        }
