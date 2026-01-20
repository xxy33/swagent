"""
示例: 工具调用演示

演示如何在Agent中使用工具系统，包括：
1. 注册工具到全局注册中心
2. Agent使用工具进行计算
3. Function Calling自动工具调用
4. 工具链式调用
"""
import asyncio
import json
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def example_1_basic_tool_usage():
    """示例1: 基础工具使用"""
    print("\n" + "=" * 60)
    print("示例1: 基础工具使用")
    print("=" * 60)

    from swagent.tools.domain import EmissionCalculator

    # 创建工具实例
    calculator = EmissionCalculator()

    # 查看工具信息
    print(f"\n工具名称: {calculator.name}")
    print(f"工具描述: {calculator.description}")
    print(f"工具类别: {calculator.category.value}")

    # 使用工具
    print("\n--- 计算垃圾焚烧的碳排放 ---")
    result = await calculator.execute(
        waste_type="food_waste",
        treatment_method="incineration",
        quantity=500  # 500吨
    )

    if result.success:
        print(f"✓ 计算成功!")
        print(f"  废物类型: {result.data['waste_type']}")
        print(f"  处理方式: {result.data['treatment_method']}")
        print(f"  废物量: {result.data['quantity_tonnes']} 吨")
        print(f"  碳排放: {result.data['total_emission_kgCO2e']} kg CO2e")
        print(f"  碳排放: {result.data['total_emission_tCO2e']} t CO2e")
    else:
        print(f"✗ 计算失败: {result.error}")


async def example_2_tool_registry():
    """示例2: 使用工具注册中心"""
    print("\n" + "=" * 60)
    print("示例2: 使用工具注册中心")
    print("=" * 60)

    from swagent.tools import ToolRegistry
    from swagent.tools.builtin import CodeExecutor, FileHandler
    from swagent.tools.domain import EmissionCalculator, LCAAnalyzer

    # 创建注册中心
    registry = ToolRegistry()

    # 批量注册工具
    registry.register(CodeExecutor())
    registry.register(FileHandler())
    registry.register(EmissionCalculator())
    registry.register(LCAAnalyzer())

    print(f"\n已注册 {len(registry)} 个工具")
    print(f"工具列表: {registry.list_tools()}")

    # 统一调用接口
    print("\n--- 通过注册中心调用工具 ---")
    result = await registry.execute_tool(
        "emission_calculator",
        waste_type="plastic",
        treatment_method="recycling",
        quantity=100
    )

    if result.success:
        print(f"✓ 工具调用成功")
        print(f"  结果: 总排放 {result.data['total_emission_kgCO2e']} kg CO2e")


async def example_3_function_calling_format():
    """示例3: Function Calling格式转换"""
    print("\n" + "=" * 60)
    print("示例3: OpenAI Function Calling格式")
    print("=" * 60)

    from swagent.tools import ToolRegistry
    from swagent.tools.domain import EmissionCalculator, LCAAnalyzer

    registry = ToolRegistry()
    registry.register(EmissionCalculator())
    registry.register(LCAAnalyzer())

    # 转换为OpenAI Function格式
    functions = registry.to_openai_functions()

    print(f"\n生成了 {len(functions)} 个Function定义")
    print("\n--- emission_calculator Function ---")
    func = functions[0]
    print(json.dumps(func, indent=2, ensure_ascii=False))


async def example_4_simulated_agent_with_tools():
    """示例4: 模拟Agent使用工具"""
    print("\n" + "=" * 60)
    print("示例4: 模拟Agent使用工具")
    print("=" * 60)

    from swagent.tools import ToolRegistry
    from swagent.tools.domain import EmissionCalculator, LCAAnalyzer

    # 设置工具
    registry = ToolRegistry()
    registry.register(EmissionCalculator())
    registry.register(LCAAnalyzer())

    # 模拟用户请求
    user_query = "帮我计算100吨食物垃圾进行堆肥处理的碳排放"

    print(f"\n用户请求: {user_query}")

    # 模拟Agent思考过程
    print("\n--- Agent思考 ---")
    print("分析: 用户需要计算碳排放")
    print("识别参数:")
    print("  - waste_type: food_waste")
    print("  - treatment_method: composting")
    print("  - quantity: 100")
    print("决策: 使用 emission_calculator 工具")

    # 调用工具
    print("\n--- 执行工具 ---")
    result = await registry.execute_tool(
        "emission_calculator",
        waste_type="food_waste",
        treatment_method="composting",
        quantity=100
    )

    # 模拟Agent生成响应
    print("\n--- Agent响应 ---")
    if result.success:
        data = result.data
        response = f"""根据计算结果：

100吨食物垃圾采用堆肥处理的碳排放为：
- 排放因子: {data['emission_factor']} kg CO2e/吨
- 总碳排放: {data['total_emission_kgCO2e']} kg CO2e ({data['total_emission_tCO2e']} 吨 CO2e)

堆肥处理相比填埋和焚烧，具有较低的温室气体排放，是处理有机废物的环保选择。"""
        print(response)


async def example_5_tool_chain():
    """示例5: 工具链式调用"""
    print("\n" + "=" * 60)
    print("示例5: 工具链式调用")
    print("=" * 60)

    from swagent.tools import ToolRegistry
    from swagent.tools.domain import EmissionCalculator, LCAAnalyzer, Visualizer

    registry = ToolRegistry()
    registry.register(EmissionCalculator())
    registry.register(LCAAnalyzer())
    registry.register(Visualizer())

    # 场景：比较不同处理方式的环境影响
    print("\n场景: 比较100吨塑料的不同处理方式\n")

    treatment_methods = ["landfill", "incineration", "recycling"]
    emissions = []
    labels = []

    # 步骤1: 计算各种方式的排放
    print("步骤1: 计算各处理方式的碳排放")
    for method in treatment_methods:
        result = await registry.execute_tool(
            "emission_calculator",
            waste_type="plastic",
            treatment_method=method,
            quantity=100
        )
        if result.success:
            emission = result.data['total_emission_kgCO2e']
            emissions.append(emission)
            labels.append(method)
            print(f"  {method}: {emission} kg CO2e")

    # 步骤2: 进行LCA分析（以回收为例）
    print("\n步骤2: 进行LCA全生命周期分析")
    lca_result = await registry.execute_tool(
        "lca_analyzer",
        treatment_method="recycling",
        quantity=100,
        impact_categories=["climate_change", "energy_consumption"]
    )

    if lca_result.success:
        print(f"  综合评分: {lca_result.data['overall_score']}")
        for category, impact in lca_result.data['impacts'].items():
            print(f"  {category}: {impact['total']} {impact['unit']}")

    # 步骤3: 生成可视化图表
    print("\n步骤3: 生成对比图表")
    viz_result = await registry.execute_tool(
        "visualizer",
        chart_type="bar",
        data={
            "labels": labels,
            "values": emissions
        },
        title="不同处理方式的碳排放对比 (100吨塑料)",
        ylabel="kg CO2e",
        output_format="base64"
    )

    if viz_result.success:
        if "note" in viz_result.data:
            print(f"  生成图表配置（matplotlib未安装）")
        else:
            print(f"  生成图表成功，Base64长度: {len(viz_result.data['data'])} 字符")

    # 步骤4: 生成综合报告
    print("\n步骤4: 生成综合报告")
    report = f"""
# 100吨塑料废物处理方式对比报告

## 1. 碳排放对比
{chr(10).join([f'- {labels[i]}: {emissions[i]} kg CO2e' for i in range(len(labels))])}

## 2. 推荐方案
回收处理具有最低的碳排放（{emissions[2]} kg CO2e），相比填埋减少了 {emissions[0] - emissions[2]:.0f} kg CO2e。

## 3. LCA综合评估
- 综合评分: {lca_result.data['overall_score']}
- 环境效益: 回收避免了资源提取和加工的环境影响

## 4. 建议
优先采用回收处理，建立完善的塑料分类和回收体系。
"""
    print(report)


async def example_6_code_executor():
    """示例6: 代码执行器使用"""
    print("\n" + "=" * 60)
    print("示例6: 代码执行器 - 自动化数据分析")
    print("=" * 60)

    from swagent.tools.builtin import CodeExecutor

    executor = CodeExecutor()

    # 场景：使用Python分析垃圾处理数据
    print("\n场景: 使用Python分析垃圾处理数据\n")

    code = """
# 垃圾处理数据分析
data = {
    'landfill': {'amount': 300, 'emission_factor': 580},
    'incineration': {'amount': 400, 'emission_factor': 450},
    'recycling': {'amount': 300, 'emission_factor': -800}
}

# 计算总排放
total_emission = sum(v['amount'] * v['emission_factor'] for v in data.values())
total_amount = sum(v['amount'] for v in data.values())
avg_emission = total_emission / total_amount

print(f"总垃圾量: {total_amount} 吨")
print(f"总排放: {total_emission} kg CO2e")
print(f"平均排放强度: {avg_emission:.2f} kg CO2e/吨")

# 找出排放最高和最低的处理方式
emissions = {k: v['amount'] * v['emission_factor'] for k, v in data.items()}
highest = max(emissions.items(), key=lambda x: x[1])
lowest = min(emissions.items(), key=lambda x: x[1])

print(f"\\n最高排放: {highest[0]} ({highest[1]} kg CO2e)")
print(f"最低排放: {lowest[0]} ({lowest[1]} kg CO2e)")
"""

    result = await executor.execute(code=code, language="python")

    if result.success:
        print("执行结果:")
        print(result.data['stdout'])
    else:
        print(f"执行失败: {result.error}")


async def main():
    """运行所有示例"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "SWAgent - 工具调用演示示例" + " " * 20 + "║")
    print("╚" + "═" * 58 + "╝")

    # 运行所有示例
    await example_1_basic_tool_usage()
    await example_2_tool_registry()
    await example_3_function_calling_format()
    await example_4_simulated_agent_with_tools()
    await example_5_tool_chain()
    await example_6_code_executor()

    print("\n" + "=" * 60)
    print("所有示例演示完成!")
    print("=" * 60)
    print("\n你可以基于这些示例：")
    print("  1. 创建自己的工具")
    print("  2. 在Agent中集成工具调用")
    print("  3. 实现复杂的工具链")
    print("  4. 使用Function Calling让LLM自动选择工具")
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
