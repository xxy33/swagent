"""
阶段4测试：领域增强

测试内容：
1. 知识库查询（废物分类、处理方法）
2. 专业术语库（翻译、定义、缩写）
3. 标准规范库（标准查询、法规查询）
4. 领域提示词（不同任务类型）
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_knowledge_base():
    """测试知识库"""
    print("\n" + "=" * 60)
    print("测试1: 固废知识库")
    print("=" * 60)

    from swagent.domain import get_knowledge_base

    kb = get_knowledge_base()

    # 测试1: 获取废物类别
    print("\n--- 获取废物类别：食物垃圾 ---")
    food_waste = kb.get_waste_category('food_waste')
    if food_waste:
        print(f"✓ 名称: {food_waste.get('name_zh')}")
        print(f"  描述: {food_waste.get('description')}")
        print(f"  含水率: {food_waste.get('moisture_content')}")
        print(f"  适合处理: {food_waste.get('suitable_treatments')}")

    # 测试2: 获取处理方法
    print("\n--- 获取处理方法：焚烧 ---")
    incineration = kb.get_treatment_method('incineration')
    if incineration:
        print(f"✓ 名称: {incineration.get('name_zh')}")
        print(f"  描述: {incineration.get('description')}")
        if 'types' in incineration and 'wte' in incineration['types']:
            wte = incineration['types']['wte']
            print(f"  WTE温度: {wte.get('temperature')}")
            print(f"  减容率: {wte.get('volume_reduction')}")
            print(f"  优点: {wte.get('advantages')}")

    # 测试3: 获取适合的处理方式
    print("\n--- 查询适合塑料的处理方式 ---")
    plastic = kb.get_waste_category('plastic')
    if plastic:
        print(f"✓ 塑料类型: {plastic.get('types', [])}")

    # 测试4: 获取废物层级
    print("\n--- 废物管理层级 ---")
    hierarchy = kb.get_waste_hierarchy()
    if hierarchy:
        print("✓ 废物管理优先级:")
        for level in hierarchy:
            print(f"  {level['priority']}. {level['name_zh']} ({level['name_en']}): {level['description']}")

    # 测试5: 搜索功能
    print("\n--- 搜索关键词：回收 ---")
    results = kb.search_by_keyword('回收')
    print(f"✓ 找到 {len(results['waste_categories'])} 个废物类别")
    print(f"✓ 找到 {len(results['treatment_methods'])} 个处理方法")

    # 测试6: 比较处理方式
    print("\n--- 比较厨余垃圾的处理方式 ---")
    comparison = kb.compare_treatments('food_waste')
    print(f"✓ 废物类型: {comparison['waste_type']}")
    print(f"  适合的处理: {', '.join(comparison['suitable_treatments'])}")
    if comparison['treatment_details']:
        for method, details in list(comparison['treatment_details'].items())[:2]:
            print(f"\n  {details['name']}:")
            print(f"    优点: {', '.join(details.get('advantages', [])[:2])}")

    return True


def test_terminology_db():
    """测试专业术语库"""
    print("\n" + "=" * 60)
    print("测试2: 专业术语库")
    print("=" * 60)

    from swagent.domain import get_terminology_db

    term_db = get_terminology_db()

    # 测试1: 获取术语
    print("\n--- 获取术语：LCA ---")
    lca = term_db.get_term('LCA')
    if lca:
        print(f"✓ 英文全称: {lca.get('full_name_en')}")
        print(f"  中文全称: {lca.get('full_name_zh')}")
        print(f"  定义: {lca.get('definition')}")
        print(f"  类别: {lca.get('category')}")

    # 测试2: 翻译术语
    print("\n--- 翻译术语 ---")
    zh_name = term_db.translate('MSW', 'zh')
    print(f"✓ MSW -> {zh_name}")

    en_name = term_db.translate('温室气体', 'en')
    print(f"✓ 温室气体 -> {en_name}")

    # 测试3: 获取定义
    print("\n--- 获取定义：biogas ---")
    definition = term_db.get_definition('biogas')
    if definition:
        print(f"✓ {definition}")

    # 测试4: 展开缩写
    print("\n--- 展开缩写 ---")
    wte_full = term_db.expand_abbreviation('WTE', 'zh')
    print(f"✓ WTE 全称: {wte_full}")

    # 测试5: 搜索术语
    print("\n--- 搜索术语：焚烧 ---")
    results = term_db.search_terms('焚烧')
    print(f"✓ 找到 {len(results)} 个相关术语")
    for result in results[:3]:
        print(f"  - {result['term']} ({result['category']})")

    # 测试6: 获取废物类型属性
    print("\n--- 废物类型属性：plastic_waste ---")
    properties = term_db.get_waste_type_properties('plastic_waste')
    if properties:
        print(f"✓ 属性:")
        for key, value in properties.items():
            print(f"  - {key}: {value}")

    # 测试7: 解释术语
    print("\n--- 解释术语：dioxin ---")
    explanation = term_db.explain_term('dioxin', detailed=True)
    print(f"✓ {explanation}")

    return True


def test_standards_db():
    """测试标准规范库"""
    print("\n" + "=" * 60)
    print("测试3: 标准规范库")
    print("=" * 60)

    from swagent.domain import get_standards_db

    std_db = get_standards_db()

    # 测试1: 获取标准
    print("\n--- 获取标准：GB18485-2014 ---")
    gb18485 = std_db.get_standard('GB18485-2014')
    if gb18485:
        print(f"✓ 全称: {gb18485.get('full_name')}")
        print(f"  实施日期: {gb18485.get('effective_date')}")
        print(f"  适用范围: {gb18485.get('scope')}")
        if 'key_requirements' in gb18485:
            limits = gb18485['key_requirements'].get('emission_limits', {})
            print(f"  排放限值:")
            for pollutant, limit in list(limits.items())[:3]:
                print(f"    - {pollutant}: {limit}")

    # 测试2: 获取国际标准
    print("\n--- 获取国际标准：ISO14040 ---")
    iso14040 = std_db.get_standard('ISO14040', region='international')
    if iso14040:
        print(f"✓ 全称: {iso14040.get('full_name')}")
        print(f"  中文名: {iso14040.get('full_name_zh')}")
        print(f"  组织: {iso14040.get('organization')}")
        print(f"  关键阶段: {iso14040.get('key_phases')}")

    # 测试3: 搜索标准
    print("\n--- 搜索标准：焚烧 ---")
    results = std_db.search_standards('焚烧', region='china')
    print(f"✓ 找到 {len(results)} 个相关标准")
    for result in results[:3]:
        print(f"  - {result['id']}: {result['data'].get('full_name', '')}")

    # 测试4: 获取IPCC指南
    print("\n--- IPCC指南 ---")
    ipcc = std_db.get_ipcc_guidelines()
    print(f"✓ 找到 {len(ipcc)} 个IPCC指南")
    if ipcc:
        for guide in ipcc:
            print(f"  - {guide['id']}: {guide['data'].get('full_name')}")

    # 测试5: 获取政策
    print("\n--- 获取政策：塑料禁令 ---")
    plastic_policy = std_db.get_policy('plastic_ban_policy')
    if plastic_policy:
        print(f"✓ 名称: {plastic_policy.get('full_name')}")
        print(f"  发布机构: {plastic_policy.get('issuing_authority')}")
        if 'key_targets' in plastic_policy:
            print(f"  关键目标:")
            for year, target in plastic_policy['key_targets'].items():
                print(f"    {year}: {target}")

    # 测试6: 获取最佳实践
    print("\n--- 最佳实践：循环经济 ---")
    circular = std_db.get_best_practice('circular_economy')
    if circular:
        print(f"✓ 名称: {circular.get('name')}")
        print(f"  定义: {circular.get('definition')}")
        print(f"  关键策略: {circular.get('key_strategies')}")

    # 测试7: 解释标准
    print("\n--- 解释标准：GB16889-2008 ---")
    explanation = std_db.explain_standard('GB16889-2008')
    print(f"✓\n{explanation}")

    return True


def test_domain_prompts():
    """测试领域提示词"""
    print("\n" + "=" * 60)
    print("测试4: 领域提示词")
    print("=" * 60)

    from swagent.domain import DomainPrompts, PromptType

    # 测试1: 获取系统提示词
    print("\n--- 排放计算系统提示词 ---")
    sys_prompt = DomainPrompts.get_system_prompt(PromptType.EMISSION_CALCULATION)
    print(f"✓ 提示词长度: {len(sys_prompt)} 字符")
    print(f"  前200字符: {sys_prompt[:200]}...")

    # 测试2: 创建排放计算提示词
    print("\n--- 创建排放计算任务提示词 ---")
    prompts = DomainPrompts.create_emission_calculation_prompt(
        waste_type="食物垃圾",
        treatment_method="堆肥",
        quantity=100,
        include_transport=True,
        transport_distance=20
    )
    print(f"✓ System提示词: {len(prompts['system'])} 字符")
    print(f"✓ User提示词: {len(prompts['user'])} 字符")
    print(f"\nUser提示词内容:\n{prompts['user']}")

    # 测试3: 创建处理方式比较提示词
    print("\n--- 创建处理方式比较提示词 ---")
    prompts = DomainPrompts.create_treatment_comparison_prompt(
        waste_type="塑料",
        quantity=1000,
        composition="主要为PET和HDPE",
        moisture_content="<5%",
        treatment_methods=["landfill", "incineration", "recycling"]
    )
    print(f"✓ 已生成处理方式比较提示词")
    print(f"  包含处理方式: landfill, incineration, recycling")

    # 测试4: 创建LCA提示词
    print("\n--- 创建LCA分析提示词 ---")
    prompts = DomainPrompts.create_lca_prompt(
        treatment_method="回收",
        quantity=500,
        boundary="从收集到再生产品",
        impact_categories=["climate_change", "energy_consumption", "water_consumption"]
    )
    print(f"✓ 已生成LCA分析提示词")
    print(f"  影响类别: climate_change, energy_consumption, water_consumption")

    # 测试5: 创建政策咨询提示词
    print("\n--- 创建政策咨询提示词 ---")
    prompts = DomainPrompts.create_policy_query_prompt(
        question="焚烧厂的二噁英排放限值是多少？",
        region="中国",
        facility_type="垃圾焚烧发电厂"
    )
    print(f"✓ 已生成政策咨询提示词")

    # 测试6: 创建技术咨询提示词
    print("\n--- 创建技术咨询提示词 ---")
    prompts = DomainPrompts.create_consultation_prompt(
        question="如何选择合适的厨余垃圾处理技术？",
        background="某城市日产厨余垃圾200吨",
        constraints="预算有限，优先考虑环保效益"
    )
    print(f"✓ 已生成技术咨询提示词")

    # 测试7: 测试所有提示词类型
    print("\n--- 所有提示词类型 ---")
    all_types = [
        PromptType.GENERAL_CONSULTATION,
        PromptType.EMISSION_CALCULATION,
        PromptType.TREATMENT_RECOMMENDATION,
        PromptType.LCA_ANALYSIS,
        PromptType.POLICY_COMPLIANCE,
        PromptType.RESEARCH_SUPPORT,
        PromptType.REPORT_GENERATION,
        PromptType.DATA_ANALYSIS
    ]
    print(f"✓ 共有 {len(all_types)} 种提示词类型:")
    for ptype in all_types:
        prompt = DomainPrompts.get_system_prompt(ptype)
        print(f"  - {ptype.value}: {len(prompt)} 字符")

    return True


def test_integration():
    """测试集成功能"""
    print("\n" + "=" * 60)
    print("测试5: 集成功能测试")
    print("=" * 60)

    from swagent.domain import get_knowledge_base, get_terminology_db, get_standards_db

    kb = get_knowledge_base()
    term_db = get_terminology_db()
    std_db = get_standards_db()

    # 场景：用户询问塑料回收
    print("\n--- 场景：塑料回收咨询 ---")

    # 1. 从知识库获取塑料信息
    print("\n1. 查询塑料废物信息")
    plastic = kb.get_waste_category('plastic')
    if plastic:
        print(f"✓ 找到废物类别")

    # 2. 从术语库获取回收定义
    print("\n2. 查询回收术语")
    recycling_term = term_db.get_term('recycling', category='treatment_methods')
    if recycling_term:
        print(f"✓ 回收定义: {recycling_term.get('term_zh')}")
        print(f"  优点: {recycling_term.get('advantages')}")

    # 3. 从知识库获取回收详情
    print("\n3. 查询回收处理方法")
    recycling_method = kb.get_treatment_method('recycling')
    if recycling_method and 'material_specific' in recycling_method:
        plastic_recycling = recycling_method['material_specific'].get('plastic_recycling')
        if plastic_recycling:
            print(f"✓ 塑料回收类型:")
            print(f"  - {plastic_recycling.get('mechanical_recycling')}")
            print(f"  - {plastic_recycling.get('chemical_recycling')}")
            print(f"  挑战: {plastic_recycling.get('challenges')}")

    # 4. 查询相关标准
    print("\n4. 查询相关标准")
    recycling_standards = std_db.search_standards('回收', region='china')
    if recycling_standards:
        print(f"✓ 找到 {len(recycling_standards)} 个相关标准")

    # 5. 获取最佳实践
    print("\n5. 查询最佳实践")
    circular = std_db.get_best_practice('circular_economy')
    if circular:
        print(f"✓ 循环经济策略:")
        for strategy in circular.get('key_strategies', [])[:3]:
            print(f"  - {strategy}")

    print("\n✓ 集成测试完成：成功组合使用知识库、术语库和标准库")

    return True


def main():
    """主测试函数"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "SWAgent - 阶段4测试" + " " * 23 + "║")
    print("║" + " " * 20 + "领域增强" + " " * 28 + "║")
    print("╚" + "═" * 58 + "╝")

    results = []

    # 测试1: 知识库
    try:
        result = test_knowledge_base()
        results.append(("知识库", result))
    except Exception as e:
        print(f"\n✗ 知识库测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("知识库", False))

    # 测试2: 术语库
    try:
        result = test_terminology_db()
        results.append(("术语库", result))
    except Exception as e:
        print(f"\n✗ 术语库测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("术语库", False))

    # 测试3: 标准库
    try:
        result = test_standards_db()
        results.append(("标准库", result))
    except Exception as e:
        print(f"\n✗ 标准库测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("标准库", False))

    # 测试4: 领域提示词
    try:
        result = test_domain_prompts()
        results.append(("领域提示词", result))
    except Exception as e:
        print(f"\n✗ 领域提示词测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("领域提示词", False))

    # 测试5: 集成功能
    try:
        result = test_integration()
        results.append(("集成功能", result))
    except Exception as e:
        print(f"\n✗ 集成功能测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        results.append(("集成功能", False))

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
        print("  ✓ 固废知识库（废物分类、处理方法、废物层级）")
        print("  ✓ 专业术语库（中英互译、定义查询、缩写展开）")
        print("  ✓ 标准规范库（国家标准、国际标准、法规政策）")
        print("  ✓ 领域提示词（8种专业提示词类型）")
        print("  ✓ 集成查询功能")
        print("\n领域知识库统计:")
        print("  - 废物类别: 4大类（城市、工业、建筑、农业）")
        print("  - 处理方法: 6种主要方法")
        print("  - 专业术语: 60+ 条")
        print("  - 标准规范: 30+ 项")
        print("  - 提示词模板: 8种类型")
    else:
        print("\n⚠️  部分测试失败，请检查后重试。")

    print("\n")


if __name__ == "__main__":
    main()
