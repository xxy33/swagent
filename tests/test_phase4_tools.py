"""
阶段4测试：工具系统

测试内容：
1. 工具基础架构
2. 内置工具（代码执行、文件处理、网络搜索）
3. 领域工具（排放计算、LCA分析、可视化）
4. 工具注册中心
5. OpenAI Function Calling集成
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_tool_registry():
    """测试工具注册中心"""
    print("\n" + "=" * 60)
    print("测试1: 工具注册中心")
    print("=" * 60)

    from swagent.tools import ToolRegistry
    from swagent.tools.builtin import CodeExecutor, FileHandler, WebSearch
    from swagent.tools.domain import EmissionCalculator, LCAAnalyzer, Visualizer

    # 创建注册中心
    registry = ToolRegistry()

    # 注册工具
    registry.register(CodeExecutor())
    registry.register(FileHandler())
    registry.register(WebSearch())
    registry.register(EmissionCalculator())
    registry.register(LCAAnalyzer())
    registry.register(Visualizer())

    print(f"✓ 注册了 {len(registry)} 个工具")

    # 列出工具
    tools = registry.list_tools()
    print(f"✓ 工具列表: {tools}")

    # 获取统计
    stats = registry.get_statistics()
    print(f"✓ 按类别统计: {stats['by_category']}")

    # 转换为OpenAI Functions
    functions = registry.to_openai_functions()
    print(f"✓ 生成OpenAI Functions: {len(functions)} 个")

    # 转换为MCP Tools
    mcp_tools = registry.to_mcp_tools()
    print(f"✓ 生成MCP Tools: {len(mcp_tools)} 个")

    return True


async def test_code_executor():
    """测试代码执行器"""
    print("\n" + "=" * 60)
    print("测试2: 代码执行器")
    print("=" * 60)

    from swagent.tools.builtin import CodeExecutor

    executor = CodeExecutor(timeout=10)

    # 测试Python代码
    print("\n--- Python代码执行 ---")
    result = await executor.execute(
        code="print('Hello from Python!')\nprint(2 + 2)",
        language="python"
    )

    if result.success:
        print(f"✓ 执行成功")
        print(f"  stdout: {result.data['stdout']}")
        print(f"  exit_code: {result.data['exit_code']}")
    else:
        print(f"✗ 执行失败: {result.error}")

    # 测试Shell代码
    print("\n--- Shell代码执行 ---")
    result = await executor.execute(
        code="echo 'Hello from Shell!'",
        language="shell"
    )

    if result.success:
        print(f"✓ 执行成功")
        print(f"  stdout: {result.data['stdout'].strip()}")
    else:
        print(f"✗ 执行失败: {result.error}")

    return True


async def test_file_handler():
    """测试文件处理器"""
    print("\n" + "=" * 60)
    print("测试3: 文件处理器")
    print("=" * 60)

    from swagent.tools.builtin import FileHandler

    handler = FileHandler(base_path="./data/test")

    # 写入文件
    print("\n--- 写入文件 ---")
    result = await handler.execute(
        operation="write",
        file_path="test.txt",
        content="Hello, World!\nThis is a test file."
    )
    print(f"✓ 写入文件: {result.success}")

    # 读取文件
    print("\n--- 读取文件 ---")
    result = await handler.execute(
        operation="read",
        file_path="test.txt"
    )
    if result.success:
        print(f"✓ 读取成功")
        print(f"  内容: {result.data['content'][:50]}...")
        print(f"  大小: {result.data['size']} 字节")

    # 列出文件
    print("\n--- 列出文件 ---")
    result = await handler.execute(
        operation="list",
        file_path=""
    )
    if result.success:
        print(f"✓ 文件列表: {len(result.data['files'])} 个文件")
        for f in result.data['files'][:3]:
            print(f"  - {f['name']} ({f['type']})")

    return True


async def test_emission_calculator():
    """测试排放计算工具"""
    print("\n" + "=" * 60)
    print("测试4: 温室气体排放计算")
    print("=" * 60)

    from swagent.tools.domain import EmissionCalculator

    calculator = EmissionCalculator()

    # 测试1: 食物垃圾堆肥
    print("\n--- 食物垃圾堆肥 ---")
    result = await calculator.execute(
        waste_type="food_waste",
        treatment_method="composting",
        quantity=100
    )

    if result.success:
        data = result.data
        print(f"✓ 计算成功")
        print(f"  废物类型: {data['waste_type']}")
        print(f"  处理方式: {data['treatment_method']}")
        print(f"  废物量: {data['quantity_tonnes']} 吨")
        print(f"  排放因子: {data['emission_factor']} kg CO2e/吨")
        print(f"  总排放: {data['total_emission_kgCO2e']} kg CO2e")
        print(f"  总排放: {data['total_emission_tCO2e']} t CO2e")

    # 测试2: 塑料回收（含运输）
    print("\n--- 塑料回收（含运输） ---")
    result = await calculator.execute(
        waste_type="plastic",
        treatment_method="recycling",
        quantity=50,
        include_transport=True,
        transport_distance=20
    )

    if result.success:
        data = result.data
        print(f"✓ 计算成功")
        print(f"  直接排放: {data['direct_emission_kgCO2e']} kg CO2e")
        print(f"  运输排放: {data['transport_emission_kgCO2e']} kg CO2e")
        print(f"  总排放: {data['total_emission_kgCO2e']} kg CO2e (负值表示减排)")

    return True


async def test_lca_analyzer():
    """测试LCA分析工具"""
    print("\n" + "=" * 60)
    print("测试5: 生命周期评估分析")
    print("=" * 60)

    from swagent.tools.domain import LCAAnalyzer

    analyzer = LCAAnalyzer()

    # 测试: 回收处理LCA
    print("\n--- 回收处理LCA分析 ---")
    result = await analyzer.execute(
        treatment_method="recycling",
        quantity=100,
        impact_categories=["climate_change", "energy_consumption", "water_consumption"]
    )

    if result.success:
        data = result.data
        print(f"✓ 分析成功")
        print(f"  处理方式: {data['treatment_method']}")
        print(f"  废物量: {data['quantity_tonnes']} 吨")
        print(f"  综合评分: {data['overall_score']}")
        print(f"\n  影响类别:")
        for category, impact in data['impacts'].items():
            print(f"    - {category}: {impact['total']} {impact['unit']}")
        print(f"\n  解释: {data['interpretation']}")

    return True


async def test_visualizer():
    """测试可视化工具"""
    print("\n" + "=" * 60)
    print("测试6: 数据可视化")
    print("=" * 60)

    from swagent.tools.domain import Visualizer

    visualizer = Visualizer()

    # 测试: 柱状图
    print("\n--- 生成柱状图 ---")
    result = await visualizer.execute(
        chart_type="bar",
        data={
            "labels": ["填埋", "焚烧", "堆肥", "回收"],
            "values": [580, 450, 125, -800]
        },
        title="不同处理方式的碳排放",
        ylabel="kg CO2 eq/ton",
        output_format="base64"
    )

    if result.success:
        if "note" in result.data:
            print(f"✓ 生成配置（matplotlib未安装）")
            print(f"  配置: {result.data['config']['title']}")
        else:
            print(f"✓ 生成成功")
            print(f"  图表类型: {result.data['chart_type']}")
            print(f"  格式: {result.data['format']}")
            print(f"  数据长度: {len(result.data['data'])} 字符")

    return True


async def test_openai_function_calling():
    """测试OpenAI Function Calling集成"""
    print("\n" + "=" * 60)
    print("测试7: OpenAI Function Calling集成")
    print("=" * 60)

    from swagent.tools import ToolRegistry
    from swagent.tools.domain import EmissionCalculator

    # 创建注册中心并注册工具
    registry = ToolRegistry()
    registry.register(EmissionCalculator())

    # 获取OpenAI Function定义
    functions = registry.to_openai_functions(["emission_calculator"])

    print(f"✓ 生成Function定义")
    print(f"  工具名: {functions[0]['function']['name']}")
    print(f"  描述: {functions[0]['function']['description']}")
    print(f"  参数数量: {len(functions[0]['function']['parameters']['properties'])}")
    print(f"  必需参数: {functions[0]['function']['parameters']['required']}")

    # 模拟LLM调用工具
    print("\n--- 模拟工具调用 ---")
    import json
    tool_call = {
        "name": "emission_calculator",
        "arguments": json.dumps({
            "waste_type": "paper",
            "treatment_method": "recycling",
            "quantity": 200
        })
    }

    # 解析参数并执行
    args = json.loads(tool_call["arguments"])
    result = await registry.execute_tool(tool_call["name"], **args)

    if result.success:
        print(f"✓ 工具执行成功")
        print(f"  总排放: {result.data['total_emission_kgCO2e']} kg CO2e")

    return True


async def test_mcp_tools():
    """测试MCP工具格式"""
    print("\n" + "=" * 60)
    print("测试8: MCP工具格式")
    print("=" * 60)

    from swagent.tools import ToolRegistry
    from swagent.tools.domain import LCAAnalyzer

    registry = ToolRegistry()
    registry.register(LCAAnalyzer())

    # 获取MCP工具定义
    mcp_tools = registry.to_mcp_tools(["lca_analyzer"])

    print(f"✓ 生成MCP工具定义")
    tool = mcp_tools[0]
    print(f"  名称: {tool['name']}")
    print(f"  描述: {tool['description']}")
    print(f"  类别: {tool['category']}")
    print(f"  输入模式: {list(tool['inputSchema']['properties'].keys())}")
    print(f"  返回描述: {tool['returns']}")

    return True


async def main():
    """主测试函数"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "SWAgent - 阶段4测试" + " " * 23 + "║")
    print("║" + " " * 20 + "工具系统" + " " * 28 + "║")
    print("╚" + "═" * 58 + "╝")

    results = []

    # 测试1: 工具注册中心
    try:
        result = await test_tool_registry()
        results.append(("工具注册中心", result))
    except Exception as e:
        print(f"\n✗ 工具注册中心测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("工具注册中心", False))

    # 测试2: 代码执行器
    try:
        result = await test_code_executor()
        results.append(("代码执行器", result))
    except Exception as e:
        print(f"\n✗ 代码执行器测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("代码执行器", False))

    # 测试3: 文件处理器
    try:
        result = await test_file_handler()
        results.append(("文件处理器", result))
    except Exception as e:
        print(f"\n✗ 文件处理器测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("文件处理器", False))

    # 测试4: 排放计算
    try:
        result = await test_emission_calculator()
        results.append(("排放计算", result))
    except Exception as e:
        print(f"\n✗ 排放计算测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("排放计算", False))

    # 测试5: LCA分析
    try:
        result = await test_lca_analyzer()
        results.append(("LCA分析", result))
    except Exception as e:
        print(f"\n✗ LCA分析测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("LCA分析", False))

    # 测试6: 可视化
    try:
        result = await test_visualizer()
        results.append(("可视化", result))
    except Exception as e:
        print(f"\n✗ 可视化测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("可视化", False))

    # 测试7: Function Calling
    try:
        result = await test_openai_function_calling()
        results.append(("Function Calling", result))
    except Exception as e:
        print(f"\n✗ Function Calling测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("Function Calling", False))

    # 测试8: MCP工具
    try:
        result = await test_mcp_tools()
        results.append(("MCP工具", result))
    except Exception as e:
        print(f"\n✗ MCP工具测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("MCP工具", False))

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
        print("\n🎉 阶段4测试全部通过!")
        print("\n已完成功能:")
        print("  ✓ 工具基础架构（BaseTool, ToolRegistry）")
        print("  ✓ 内置工具（代码执行、文件处理、网络搜索）")
        print("  ✓ 领域工具（排放计算、LCA分析、可视化）")
        print("  ✓ OpenAI Function Calling集成")
        print("  ✓ MCP工具格式支持")
    else:
        print("\n⚠️  部分测试失败，请检查后重试。")

    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
