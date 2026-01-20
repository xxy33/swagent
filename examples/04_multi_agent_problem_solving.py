"""
多智能体协作问题解决示例
演示如何使用多个专业Agent协作解决复杂问题
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from swagent.core import Orchestrator, OrchestrationMode
from swagent.agents import ReActAgent
from swagent.llm import OpenAIClient, LLMConfig
from swagent.core.orchestrator import TaskDefinition


async def enterprise_tech_decision():
    """
    场景1: 企业技术选型决策
    参与者: CTO、环保专家、财务总监、运营经理
    """
    print("\n" + "=" * 80)
    print("场景1: 企业技术选型决策")
    print("=" * 80)

    # 配置LLM - 使用None让OpenAIClient自动从配置文件加载
    llm = OpenAIClient()  # 自动从config.yaml和.env加载配置

    # 创建不同角色的专业Agent
    from swagent.core.base_agent import AgentConfig

    cto_config = AgentConfig(
        name="技术总监",
        role="CTO",
        system_prompt="""你是企业的CTO，专注于技术可行性、系统稳定性和长期维护。
        你需要从技术角度评估方案，关注实施难度、技术成熟度、可扩展性。"""
    )
    cto = ReActAgent(cto_config)
    cto.llm = llm

    env_config = AgentConfig(
        name="环保专家",
        role="环境工程师",
        system_prompt="""你是环保领域专家，关注环境影响、排放标准、可持续性。
        你需要评估方案的环保性能、合规性和社会责任。"""
    )
    env_expert = ReActAgent(env_config)
    env_expert.llm = llm

    cfo_config = AgentConfig(
        name="财务总监",
        role="CFO",
        system_prompt="""你是财务总监，关注成本效益、投资回报、财务风险。
        你需要从财务角度评估方案的经济可行性和长期收益。"""
    )
    cfo = ReActAgent(cfo_config)
    cfo.llm = llm

    ops_config = AgentConfig(
        name="运营经理",
        role="运营负责人",
        system_prompt="""你是运营经理，关注实施可行性、操作便利性、人员培训。
        你需要评估方案的实际可操作性和运营风险。"""
    )
    ops_manager = ReActAgent(ops_config)
    ops_manager.llm = llm

    # 创建编排器(辩论模式)
    orchestrator = Orchestrator(mode=OrchestrationMode.DEBATE)

    # 注册所有Agent
    orchestrator.register_agent(cto)
    orchestrator.register_agent(env_expert)
    orchestrator.register_agent(cfo)
    orchestrator.register_agent(ops_manager)

    # 启动协作
    await orchestrator.start()

    # 定义问题
    problem = """
    我们公司需要为新工厂选择固体废物处理技术方案。目前有三个候选方案:

    A. 垃圾分类回收 + 堆肥系统
       - 初期投资: 500万元
       - 运营成本: 低
       - 环保性: 优秀
       - 技术成熟度: 高
       - 实施周期: 6个月

    B. 焚烧发电系统
       - 初期投资: 2000万元
       - 运营成本: 中等
       - 环保性: 良好(需严格监管)
       - 技术成熟度: 高
       - 实施周期: 12个月
       - 收益: 可发电售电

    C. 厌氧消化制沼气
       - 初期投资: 1200万元
       - 运营成本: 中等
       - 环保性: 优秀
       - 技术成熟度: 中等
       - 实施周期: 9个月
       - 收益: 沼气可利用

    请各位专家从自己的角度分析，最终达成最优方案。
    """

    # 执行辩论(带智能判断)
    judge_config = AgentConfig(
        name="决策顾问",
        role="顾问",
        system_prompt="你是中立的决策顾问，负责判断讨论何时达成共识。"
    )
    judge = ReActAgent(judge_config)
    judge.llm = llm

    result = await orchestrator.debate_with_judgment(
        topic=problem,
        max_rounds=5,
        judge_agent=judge
    )

    # 输出结果
    print("\n" + "=" * 80)
    print("讨论总结")
    print("=" * 80)
    print(f"\n讨论轮数: {result['total_rounds']}")
    print(f"是否达成共识: {'是' if result['terminated_by_judgment'] else '否'}")

    if result['judgment']:
        judgment = result['judgment']
        print(f"\n最终决策: {judgment.decision.value}")
        print(f"置信度: {judgment.confidence:.0%}")
        print(f"\n决策理由:\n{judgment.reason}")

        if judgment.suggestions:
            print("\n实施建议:")
            for i, suggestion in enumerate(judgment.suggestions, 1):
                print(f"{i}. {suggestion}")

    print("\n详细讨论记录:")
    print("-" * 80)
    for i, msg in enumerate(result['history'][:6], 1):  # 只显示前6条
        print(f"\n[{msg['agent']}]:")
        print(f"{msg['content'][:200]}...")

    return result


async def government_policy_consultation():
    """
    场景2: 政府政策制定咨询
    参与者: 政策专家、法律顾问、社会学家、环保局代表
    """
    print("\n\n" + "=" * 80)
    print("场景2: 政府政策制定咨询")
    print("=" * 80)

    llm = OpenAIClient()  # 自动从配置加载

    # 创建专家组
    from swagent.core.base_agent import AgentConfig

    policy_config = AgentConfig(
        name="政策研究员",
        role="政策专家",
        system_prompt="你是公共政策专家，关注政策可行性、社会影响、执行效果。"
    )
    policy_expert = ReActAgent(policy_config)
    policy_expert.llm = llm

    legal_config = AgentConfig(
        name="法律顾问",
        role="律师",
        system_prompt="你是法律专家，关注法律合规性、条款严谨性、执法可操作性。"
    )
    legal_advisor = ReActAgent(legal_config)
    legal_advisor.llm = llm

    socio_config = AgentConfig(
        name="社会学家",
        role="社会研究者",
        system_prompt="你是社会学家，关注公众接受度、社会公平性、行为改变机制。"
    )
    sociologist = ReActAgent(socio_config)
    sociologist.llm = llm

    env_config = AgentConfig(
        name="环保局代表",
        role="环保官员",
        system_prompt="你代表环保部门，关注环境目标、执行标准、监管机制。"
    )
    env_officer = ReActAgent(env_config)
    env_officer.llm = llm

    # 使用协作模式
    orchestrator = Orchestrator(mode=OrchestrationMode.COLLABORATIVE)

    for agent in [policy_expert, legal_advisor, sociologist, env_officer]:
        orchestrator.register_agent(agent)

    await orchestrator.start()

    # 定义咨询问题
    policy_question = """
    我市计划实施强制性垃圾分类政策，请从各自专业角度提供建议:

    1. 政策应该包含哪些核心条款？
    2. 如何确保政策的可执行性？
    3. 如何提高公众参与度和配合度？
    4. 需要哪些配套措施和资源？
    5. 如何评估政策实施效果？

    请提供具体、可操作的建议。
    """

    # 执行协作任务
    task = TaskDefinition(
        name="垃圾分类政策咨询",
        description=policy_question,
        metadata={"domain": "public_policy", "priority": "high"}
    )

    result = await orchestrator.execute(task, timeout=300)

    # 整理专家意见
    print("\n" + "=" * 80)
    print("政策咨询专家意见汇总")
    print("=" * 80)

    for expert_opinion in result.output:
        print(f"\n【{expert_opinion['agent']}】")
        print("-" * 80)
        print(expert_opinion['response'][:300] + "...")

    return result


async def academic_research_discussion():
    """
    场景3: 学术研究问题分析
    参与者: 环境工程师、数据科学家、经济学家、生态学家
    """
    print("\n\n" + "=" * 80)
    print("场景3: 学术研究问题分析")
    print("=" * 80)

    llm = OpenAIClient()  # 自动从配置加载

    # 创建研究团队
    from swagent.core.base_agent import AgentConfig

    eng_config = AgentConfig(
        name="环境工程师",
        role="工程技术专家",
        system_prompt="""你是环境工程专家，擅长废物处理技术、工艺设计、工程实施。
        从技术角度分析研究问题。"""
    )
    env_engineer = ReActAgent(eng_config)
    env_engineer.llm = llm

    ds_config = AgentConfig(
        name="数据科学家",
        role="数据分析专家",
        system_prompt="""你是数据科学家，擅长建模、统计分析、机器学习。
        从数据和模型角度分析问题。"""
    )
    data_scientist = ReActAgent(ds_config)
    data_scientist.llm = llm

    econ_config = AgentConfig(
        name="环境经济学家",
        role="经济学专家",
        system_prompt="""你是环境经济学家，擅长成本效益分析、环境经济评估。
        从经济学角度分析问题。"""
    )
    economist = ReActAgent(econ_config)
    economist.llm = llm

    eco_config = AgentConfig(
        name="生态学家",
        role="生态学专家",
        system_prompt="""你是生态学家，擅长环境影响评估、生态风险分析。
        从生态和环境角度分析问题。"""
    )
    ecologist = ReActAgent(eco_config)
    ecologist.llm = llm

    # 创建协调器
    orchestrator = Orchestrator(mode=OrchestrationMode.DEBATE)
    orchestrator.register_agent(env_engineer)
    orchestrator.register_agent(data_scientist)
    orchestrator.register_agent(economist)
    orchestrator.register_agent(ecologist)

    await orchestrator.start()

    # 研究问题
    research_question = """
    研究课题: "城市有机废物资源化处理的环境-经济综合评估模型"

    核心问题:
    1. 如何构建一个综合评估模型，同时考虑环境效益和经济效益？
    2. 模型应该包含哪些关键变量和指标？
    3. 如何获取和处理所需数据？
    4. 如何验证模型的准确性和适用性？

    请各位专家从自己的学科角度提供见解和建议。
    """

    # 执行学术讨论
    result = await orchestrator.debate_with_judgment(
        topic=research_question,
        max_rounds=4
    )

    print("\n" + "=" * 80)
    print("学术讨论总结")
    print("=" * 80)
    print(f"\n讨论轮数: {result['total_rounds']}")
    print(f"总消息数: {result['total_messages']}")

    print("\n关键讨论内容:")
    print("-" * 80)
    for msg in result['history'][:8]:  # 显示前8条
        print(f"\n[{msg['agent']}]:")
        print(f"{msg['content'][:250]}...")

    return result


async def main():
    """主函数"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "多智能体协作问题解决示例" + " " * 28 + "║")
    print("╚" + "═" * 78 + "╝")

    # 示例1: 企业技术决策
    await enterprise_tech_decision()

    # 示例2: 政府政策咨询
    await government_policy_consultation()

    # 示例3: 学术研究讨论
    await academic_research_discussion()

    print("\n\n" + "=" * 80)
    print("✓ 所有示例运行完成")
    print("=" * 80)
    print("\n核心功能:")
    print("  1. 多角色专家协作 - 模拟不同领域专家思维")
    print("  2. 深度辩论机制 - 结构化讨论挖掘问题本质")
    print("  3. 智能共识达成 - 自动识别分歧并引导共识")
    print("  4. 决策支持 - 提供多维度分析和建议")
    print()


if __name__ == "__main__":
    asyncio.run(main())
