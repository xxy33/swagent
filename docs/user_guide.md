# SWAgent 用户指南

欢迎使用 SWAgent！本指南将详细介绍系统的各个功能模块及使用方法。

## 目录

1. [快速开始](#快速开始)
2. [LLM配置](#llm配置)
3. [Agent使用](#agent使用)
4. [工具系统](#工具系统)
5. [领域知识库](#领域知识库)
6. [工作流模板](#工作流模板)
7. [多Agent协作](#多agent协作)
8. [最佳实践](#最佳实践)
9. [常见问题](#常见问题)

---

## 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/yourusername/swagent.git
cd swagent

# 安装依赖
pip install -r requirements.txt
```

### 配置环境变量

创建 `.env` 文件：

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
DEFAULT_MODEL=gpt-4
DEFAULT_TEMPERATURE=0.7
```

### 第一个程序

```python
import asyncio
from swagent.agent import ReActAgent
from swagent.llm import OpenAIClient, LLMConfig

async def main():
    # 配置LLM
    config = LLMConfig(
        provider="openai",
        model="gpt-4",
        api_key="your_api_key"
    )
    llm = OpenAIClient(config)

    # 创建Agent
    agent = ReActAgent("助手", llm=llm)

    # 执行任务
    result = await agent.execute("请介绍一下固体废物管理")
    print(result)

asyncio.run(main())
```

---

## LLM配置

### 基本配置

```python
from swagent.llm import LLMConfig, OpenAIClient

config = LLMConfig(
    provider="openai",          # 提供商
    model="gpt-4",              # 模型名称
    api_key="your_key",         # API密钥
    base_url="https://...",     # API地址
    temperature=0.7,            # 温度参数 (0.0-2.0)
    max_tokens=4096,            # 最大token数
    top_p=1.0,                  # Top-p采样
    timeout=60,                 # 超时时间(秒)
    max_retries=3,              # 最大重试次数
    stream=False                # 是否流式输出
)

llm = OpenAIClient(config)
```

### 使用本地模型

```python
config = LLMConfig(
    provider="openai",
    model="local-model",
    api_key="none",  # 本地模型可能不需要
    base_url="http://localhost:8000/v1"  # 本地API地址
)
```

### 流式输出

```python
config = LLMConfig(
    provider="openai",
    model="gpt-4",
    api_key="your_key",
    stream=True
)

llm = OpenAIClient(config)

async for chunk in llm.chat_stream(messages):
    print(chunk, end='', flush=True)
```

---

## Agent使用

### PlannerAgent - 任务规划

PlannerAgent 专注于任务规划和分解。

```python
from swagent.agent import PlannerAgent

# 创建Agent
planner = PlannerAgent("规划师", llm=llm)

# 规划任务
plan = await planner.plan("设计一个厨余垃圾处理方案")

# 执行规划的任务
result = await planner.execute("设计一个厨余垃圾处理方案")
```

**输出示例：**
```
规划步骤：
1. 分析厨余垃圾特性
2. 评估可行的处理技术
3. 经济性分析
4. 环境影响评估
5. 推荐方案
```

### ReActAgent - 推理-行动循环

ReActAgent 使用推理-行动循环，适合需要多步思考的任务。

```python
from swagent.agent import ReActAgent

# 创建Agent
react = ReActAgent("分析师", llm=llm, max_iterations=5)

# 执行任务
result = await react.execute("比较填埋和焚烧的优缺点")
```

**ReAct循环：**
```
思考：我需要分别分析填埋和焚烧的特点
行动：查询知识库获取两种方法的信息
观察：获得了处理方法的详细信息
思考：现在可以进行对比分析
行动：生成对比表格
```

### 自定义Agent行为

```python
# 设置系统提示
planner = PlannerAgent(
    "专家",
    llm=llm,
    system_prompt="你是固体废物管理领域的专家..."
)

# 设置温度参数（影响创造性）
react = ReActAgent(
    "创意助手",
    llm=llm,
    temperature=0.9  # 更高的创造性
)

# 设置最大迭代次数
react = ReActAgent(
    "深度分析师",
    llm=llm,
    max_iterations=10  # 更多的思考步骤
)
```

---

## 工具系统

### 工具注册和使用

```python
from swagent.tools import ToolRegistry
from swagent.tools.domain import EmissionCalculator, LCAAnalyzer

# 创建注册中心
registry = ToolRegistry()

# 注册工具
registry.register(EmissionCalculator())
registry.register(LCAAnalyzer())

# 列出所有工具
tools = registry.list_tools()
print(f"可用工具: {tools}")

# 执行工具
result = await registry.execute_tool(
    "emission_calculator",
    waste_type="food_waste",
    treatment_method="composting",
    quantity=100
)

print(f"排放量: {result.data['total_emission_kgCO2e']} kg CO2e")
```

### 内置工具

#### 1. 代码执行器

```python
from swagent.tools.builtin import CodeExecutor

executor = CodeExecutor(timeout=10)

# 执行Python代码
result = await executor.execute(
    code="""
data = [1, 2, 3, 4, 5]
mean = sum(data) / len(data)
print(f"平均值: {mean}")
""",
    language="python"
)

if result.success:
    print(result.data['stdout'])
```

#### 2. 文件处理器

```python
from swagent.tools.builtin import FileHandler

handler = FileHandler(base_path="./data")

# 写入文件
await handler.execute(
    operation="write",
    file_path="report.txt",
    content="报告内容..."
)

# 读取文件
result = await handler.execute(
    operation="read",
    file_path="report.txt"
)

# 列出文件
result = await handler.execute(
    operation="list",
    file_path=""
)
```

#### 3. 网络搜索

```python
from swagent.tools.builtin import WebSearch

search = WebSearch()

result = await search.execute(
    query="固体废物管理最新政策",
    max_results=5
)
```

### 领域工具

#### 1. 排放计算器

```python
from swagent.tools.domain import EmissionCalculator

calculator = EmissionCalculator()

# 基本计算
result = await calculator.execute(
    waste_type="plastic",           # 废物类型
    treatment_method="recycling",   # 处理方法
    quantity=100                    # 数量(吨)
)

print(f"直接排放: {result.data['direct_emission_kgCO2e']} kg CO2e")

# 包含运输排放
result = await calculator.execute(
    waste_type="food_waste",
    treatment_method="composting",
    quantity=200,
    include_transport=True,
    transport_distance=50  # 运输距离(km)
)

print(f"总排放: {result.data['total_emission_kgCO2e']} kg CO2e")
print(f"  - 处理排放: {result.data['direct_emission_kgCO2e']}")
print(f"  - 运输排放: {result.data['transport_emission_kgCO2e']}")
```

**支持的废物类型：**
- `food_waste` - 食物垃圾
- `plastic` - 塑料
- `paper` - 纸张
- `metal` - 金属
- `glass` - 玻璃

**支持的处理方法：**
- `landfill` - 填埋
- `incineration` - 焚烧
- `composting` - 堆肥
- `anaerobic_digestion` - 厌氧消化
- `recycling` - 回收

#### 2. LCA分析器

```python
from swagent.tools.domain import LCAAnalyzer

analyzer = LCAAnalyzer()

result = await analyzer.execute(
    treatment_method="recycling",
    quantity=100,
    impact_categories=[
        "climate_change",
        "energy_consumption",
        "water_consumption"
    ]
)

print(f"综合评分: {result.data['overall_score']}")
for category, impact in result.data['impacts'].items():
    print(f"{category}: {impact['total']} {impact['unit']}")
```

#### 3. 可视化工具

```python
from swagent.tools.domain import Visualizer

visualizer = Visualizer()

# 柱状图
result = await visualizer.execute(
    chart_type="bar",
    data={
        "labels": ["填埋", "焚烧", "堆肥", "回收"],
        "values": [580, 450, 125, -800]
    },
    title="不同处理方式的碳排放",
    ylabel="kg CO2e/ton",
    output_format="base64"  # 或 "file"
)
```

### Agent使用工具

```python
from swagent.agent import ReActAgent
from swagent.tools import ToolRegistry
from swagent.tools.domain import EmissionCalculator

# 创建工具注册中心
registry = ToolRegistry()
registry.register(EmissionCalculator())

# 创建支持工具的Agent
agent = ReActAgent("助手", llm=llm, tool_registry=registry)

# Agent会自动调用工具
result = await agent.execute(
    "帮我计算100吨塑料回收的碳排放"
)
```

### 自定义工具

```python
from swagent.tools import BaseTool, ToolSchema, ToolResult, ToolCategory

class MyCustomTool(BaseTool):
    def __init__(self):
        schema = ToolSchema(
            name="my_tool",
            description="我的自定义工具",
            category=ToolCategory.DOMAIN,
            parameters={
                "input": {
                    "type": "string",
                    "description": "输入参数",
                    "required": True
                }
            },
            returns="string"
        )
        super().__init__(schema)

    async def execute(self, **kwargs) -> ToolResult:
        input_value = kwargs.get("input")

        # 工具逻辑
        result = f"处理结果: {input_value}"

        return ToolResult(
            success=True,
            data={"output": result}
        )

# 注册自定义工具
registry.register(MyCustomTool())
```

---

## 领域知识库

### 固废知识库

```python
from swagent.domain import get_knowledge_base

kb = get_knowledge_base()

# 1. 查询废物类别
food_waste = kb.get_waste_category('food_waste')
print(f"名称: {food_waste['name_zh']}")
print(f"成分: {food_waste['composition']}")
print(f"含水率: {food_waste['moisture_content']}")
print(f"适合处理: {food_waste['suitable_treatments']}")

# 2. 查询处理方法
anaerobic = kb.get_treatment_method('anaerobic_digestion')
print(f"名称: {anaerobic['name_zh']}")
print(f"产品: {anaerobic['products']}")
print(f"优点: {anaerobic['advantages']}")

# 3. 查询适合的处理方式
suitable = kb.get_suitable_treatments('food_waste')
print(f"食物垃圾适合: {suitable}")

# 4. 查询废物层级
hierarchy = kb.get_waste_hierarchy()
for level in hierarchy:
    print(f"{level['priority']}. {level['name_zh']}: {level['description']}")

# 5. 比较处理方式
comparison = kb.compare_treatments('food_waste')
print(comparison)

# 6. 搜索
results = kb.search_by_keyword('回收')
print(f"找到 {len(results['waste_categories'])} 个废物类别")
print(f"找到 {len(results['treatment_methods'])} 个处理方法")

# 7. 获取回收信息
plastic_recycling = kb.get_recycling_info('plastic')
print(f"塑料回收: {plastic_recycling}")
```

### 专业术语库

```python
from swagent.domain import get_terminology_db

term_db = get_terminology_db()

# 1. 翻译术语
zh = term_db.translate('MSW', 'zh')
print(f"MSW = {zh}")  # MSW = 城市生活垃圾

en = term_db.translate('温室气体', 'en')
print(f"温室气体 = {en}")  # 温室气体 = Greenhouse Gas

# 2. 展开缩写
full_name = term_db.expand_abbreviation('WTE', 'zh')
print(f"WTE = {full_name}")  # WTE = 垃圾焚烧发电

# 3. 获取定义
definition = term_db.get_definition('biogas')
print(definition)

# 4. 解释术语
explanation = term_db.explain_term('leachate', detailed=True)
print(explanation)

# 5. 搜索术语
results = term_db.search_terms('焚烧')
for result in results:
    print(f"{result['term']} ({result['category']})")

# 6. 获取相关术语
related = term_db.get_related_terms('biogas')
print(f"相关术语: {related}")

# 7. 获取废物类型属性
properties = term_db.get_waste_type_properties('plastic_waste')
print(f"塑料属性: {properties}")
```

### 标准规范库

```python
from swagent.domain import get_standards_db

std_db = get_standards_db()

# 1. 查询标准
gb18485 = std_db.get_standard('GB18485-2014')
print(f"标准: {gb18485['full_name']}")
print(f"实施日期: {gb18485['effective_date']}")
print(f"排放限值: {gb18485['key_requirements']['emission_limits']}")

# 2. 查询国际标准
iso14040 = std_db.get_standard('ISO14040', region='international')
print(f"ISO14040: {iso14040['full_name_zh']}")

# 3. 搜索标准
results = std_db.search_standards('焚烧', region='china')
for result in results:
    print(f"{result['id']}: {result['data']['full_name']}")

# 4. 获取IPCC指南
ipcc = std_db.get_ipcc_guidelines()
for guide in ipcc:
    print(f"{guide['id']}: {guide['data']['full_name']}")

# 5. 查询政策
policy = std_db.get_policy('carbon_neutrality_target')
print(f"目标: {policy['targets']}")

# 6. 获取最佳实践
circular = std_db.get_best_practice('circular_economy')
print(f"循环经济: {circular['definition']}")
print(f"策略: {circular['key_strategies']}")

# 7. 解释标准
explanation = std_db.explain_standard('GB16889-2008')
print(explanation)
```

### 领域提示词

```python
from swagent.domain import DomainPrompts, PromptType

# 1. 获取系统提示词
sys_prompt = DomainPrompts.get_system_prompt(
    PromptType.EMISSION_CALCULATION
)

# 2. 生成排放计算提示词
prompts = DomainPrompts.create_emission_calculation_prompt(
    waste_type="厨余垃圾",
    treatment_method="厌氧消化",
    quantity=200,
    include_transport=True,
    transport_distance=15
)

print("System:", prompts['system'])
print("User:", prompts['user'])

# 3. 生成处理方式比较提示词
prompts = DomainPrompts.create_treatment_comparison_prompt(
    waste_type="塑料",
    quantity=1000,
    composition="主要为PET和HDPE",
    moisture_content="<5%",
    treatment_methods=["landfill", "incineration", "recycling"]
)

# 4. 生成LCA分析提示词
prompts = DomainPrompts.create_lca_prompt(
    treatment_method="回收",
    quantity=500,
    boundary="从收集到再生产品",
    impact_categories=["climate_change", "energy_consumption"]
)

# 5. 生成政策咨询提示词
prompts = DomainPrompts.create_policy_query_prompt(
    question="焚烧厂的二噁英排放限值是多少？",
    region="中国",
    facility_type="垃圾焚烧发电厂"
)

# 6. 生成技术咨询提示词
prompts = DomainPrompts.create_consultation_prompt(
    question="如何选择合适的厨余垃圾处理技术？",
    background="某城市日产厨余垃圾200吨",
    constraints="预算有限，优先考虑环保效益"
)
```

---

## 工作流模板

### 工作流管理器

```python
from swagent.workflows import get_workflow_manager

manager = get_workflow_manager()

# 1. 列出所有工作流
workflows = manager.list_workflows()
for wf in workflows:
    print(f"{wf['name']}: {wf['title']} ({wf['steps']}步)")

# 2. 获取工作流实例
research_wf = manager.get_workflow('research')

# 3. 查看工作流步骤
steps = manager.get_workflow_steps('research')
for step in steps:
    print(f"- {step['name']}: {step['description']}")
    print(f"  输入: {step['required_inputs']}")
    print(f"  输出: {step['outputs']}")

# 4. 推荐工作流
recommendations = manager.get_workflow_by_purpose("我要写一篇论文")
print(f"推荐工作流: {recommendations}")
```

### 科研工作流

```python
from swagent.workflows import ResearchWorkflow

# 创建工作流
workflow = ResearchWorkflow()

# 设置初始上下文
initial_context = {
    'research_topic': '固体废物厌氧消化技术',
    'keywords': ['厌氧消化', '沼气', '有机废物', '能源回收'],
    'time_range': '2020-2024',
    'methodology_preference': 'mixed'
}

# 执行工作流
result = await workflow.execute(initial_context)

# 查看结果
print(f"成功: {result.success}")
print(f"完成率: {result.completion_rate * 100}%")
print(f"执行时长: {result.duration}秒")

# 获取各步骤输出
if result.context.has('literature_summary'):
    print(result.context.get('literature_summary'))

if result.context.has('final_conclusions'):
    print(result.context.get('final_conclusions'))

if result.context.has('paper_draft'):
    print(result.context.get('paper_draft'))
```

**工作流步骤：**
1. literature_review - 文献调研
2. research_design - 研究设计
3. data_collection - 数据收集
4. data_analysis - 数据分析
5. result_interpretation - 结果解释
6. paper_writing - 论文撰写
7. conclusion_summary - 结论总结

### 报告生成工作流

```python
from swagent.workflows import ReportWorkflow

workflow = ReportWorkflow()

initial_context = {
    'report_type': 'technical',  # technical, assessment, project, annual
    'report_purpose': '总结2024年度固废处理项目执行情况',
    'target_audience': '管理层',
    'template': 'standard'
}

result = await workflow.execute(initial_context)

if result.success:
    final_report = result.context.get('final_report')
    print(f"报告质量: {final_report['quality_score']}/100")
    print(f"报告状态: {final_report['status']}")
    print(final_report['content'])
```

**工作流步骤：**
1. requirement_analysis - 需求分析
2. data_collection - 数据收集
3. data_organization - 数据整理
4. content_writing - 内容撰写
5. chart_generation - 图表生成
6. formatting - 格式排版
7. quality_check - 质量检查

### 数据分析工作流

```python
from swagent.workflows import DataAnalysisWorkflow

workflow = DataAnalysisWorkflow()

initial_context = {
    'data_source': 'waste_management_2024.csv',
    'file_format': 'csv',
    'exploration_depth': 'detailed'
}

result = await workflow.execute(initial_context)

# 获取关键发现
if result.context.has('key_findings'):
    findings = result.context.get('key_findings')
    for finding in findings:
        print(f"- {finding}")

# 获取可视化
if result.context.has('visualizations'):
    viz = result.context.get('visualizations')
    print(f"生成了 {len(viz)} 个图表")
```

**工作流步骤：**
1. data_import - 数据导入
2. data_exploration - 数据探索
3. data_cleaning - 数据清洗
4. feature_engineering - 特征工程
5. statistical_analysis - 统计分析
6. visualization - 可视化
7. report_generation - 报告生成

### 代码开发工作流

```python
from swagent.workflows import CodingWorkflow

workflow = CodingWorkflow()

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

# 查看测试结果
if result.context.has('unit_test_results'):
    tests = result.context.get('unit_test_results')
    print(f"测试通过: {tests['passed']}/{tests['total_tests']}")
    print(f"覆盖率: {tests['coverage']}%")

# 查看代码审查
if result.context.has('review_report'):
    review = result.context.get('review_report')
    print(f"代码质量: {review['overall_score']}/100")
```

**工作流步骤：**
1. requirement_analysis - 需求分析
2. design - 设计方案
3. implementation - 编码实现
4. unit_testing - 单元测试
5. code_review - 代码审查
6. integration_testing - 集成测试
7. documentation - 文档编写

### 使用工作流管理器执行

```python
from swagent.workflows import get_workflow_manager

manager = get_workflow_manager()

# 直接执行工作流
result = await manager.execute_workflow(
    'research',
    initial_context={
        'research_topic': '固废处理技术',
        'keywords': ['技术', '环境']
    }
)

# 从特定步骤开始执行
workflow = manager.get_workflow('analysis')
result = await workflow.execute_from_step(
    'statistical_analysis',
    initial_context={...}
)
```

---

## 多Agent协作

### 编排器

```python
from swagent.agent import Orchestrator, PlannerAgent, ReActAgent

# 创建编排器
orchestrator = Orchestrator(llm=llm)

# 添加Agent
planner = PlannerAgent("规划师", llm=llm)
analyst = ReActAgent("分析师", llm=llm)

orchestrator.add_agent(planner)
orchestrator.add_agent(analyst)

# 顺序执行
result = await orchestrator.sequential_execute(
    "分析固废管理方案",
    agents=[planner, analyst]
)

# 并行执行
results = await orchestrator.parallel_execute(
    "评估不同处理方法",
    agents=[analyst1, analyst2, analyst3]
)

# 投票决策
decision = await orchestrator.vote(
    "选择最佳处理方案",
    options=["填埋", "焚烧", "回收"]
)
```

### 辩论模式

```python
# Agent辩论
result = await orchestrator.debate(
    topic="填埋 vs 焚烧：哪个更环保？",
    rounds=3
)

print("辩论结果:")
for round_result in result:
    print(f"\n第{round_result['round']}轮:")
    for arg in round_result['arguments']:
        print(f"  {arg['agent']}: {arg['content']}")
```

### 共识机制

```python
# 达成共识
consensus = await orchestrator.reach_consensus(
    "确定最佳废物处理策略",
    max_rounds=5,
    threshold=0.8  # 80%同意即达成共识
)

print(f"共识: {consensus['agreement']}")
print(f"支持率: {consensus['support_rate']*100}%")
```

---

## 最佳实践

### 1. 错误处理

```python
from swagent.tools import ToolResult

try:
    result = await calculator.execute(
        waste_type="invalid_type",
        treatment_method="composting",
        quantity=100
    )

    if not result.success:
        print(f"错误: {result.error}")
except Exception as e:
    print(f"异常: {str(e)}")
```

### 2. 上下文管理

```python
from swagent.workflows import WorkflowContext

# 创建上下文
context = WorkflowContext()

# 设置数据
context.set('key', 'value')
context.update({'key1': 'value1', 'key2': 'value2'})

# 获取数据
value = context.get('key', default='default_value')

# 检查键
if context.has('key'):
    print("Key exists")
```

### 3. 性能优化

```python
# 1. 使用缓存（如果适用）
# 2. 批量处理数据
# 3. 异步并发执行

import asyncio

# 并发执行多个任务
tasks = [
    calculator.execute(waste_type="plastic", treatment_method="recycling", quantity=100),
    calculator.execute(waste_type="paper", treatment_method="recycling", quantity=200),
    calculator.execute(waste_type="metal", treatment_method="recycling", quantity=50)
]

results = await asyncio.gather(*tasks)
```

### 4. 日志记录

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("开始执行工作流")
result = await workflow.execute(context)
logger.info(f"工作流完成: {result.success}")
```

---

## 常见问题

### Q1: 如何使用自己的API端点？

```python
config = LLMConfig(
    provider="openai",
    model="your-model",
    api_key="your-key",
    base_url="http://your-server.com/v1"  # 自定义endpoint
)
```

### Q2: 如何处理超时？

```python
config = LLMConfig(
    provider="openai",
    model="gpt-4",
    api_key="your-key",
    timeout=120,  # 增加超时时间到120秒
    max_retries=5  # 增加重试次数
)
```

### Q3: 工作流执行失败怎么办？

```python
# 允许部分失败继续执行
result = await workflow.execute(
    initial_context,
    stop_on_error=False  # 不在错误时停止
)

# 检查每个步骤的状态
for step_result in result.step_results:
    if step_result['status'] == 'failed':
        print(f"步骤失败: {step_result['name']}")
        print(f"错误: {step_result['error']}")
```

### Q4: 如何扩展知识库？

```python
# 可以直接编辑JSON文件
# swagent/domain/data/waste_categories.json
# swagent/domain/data/treatment_methods.json
# swagent/domain/data/terminology.json
# swagent/domain/data/standards.json

# 或者在代码中动态添加
kb = get_knowledge_base()
# 知识库会自动加载JSON文件
```

### Q5: 如何调试Agent行为？

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 检查Agent输出
result = await agent.execute("任务")
print(f"Agent响应: {result}")

# 使用ReActAgent查看思考过程
react = ReActAgent("调试", llm=llm, verbose=True)
```

---

## 下一步

- 查看 [API参考](api_reference.md) 了解详细API
- 查看 [架构设计](architecture.md) 了解系统架构
- 查看示例代码 `examples/` 获取更多用法
- 加入我们的社区讨论

---

**如有问题，请提交 [Issue](https://github.com/yourusername/swagent/issues)**
