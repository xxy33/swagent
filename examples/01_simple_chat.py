"""
简单对话示例
演示如何使用PlannerAgent进行对话
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from swagent import PlannerAgent, Message, MessageType


async def main():
    """简单对话示例"""

    # 1. 创建Agent
    print("=" * 60)
    print("创建PlannerAgent...")
    print("=" * 60)

    agent = PlannerAgent.create(name="垃圾处理顾问")

    print(f"✓ Agent已创建")
    print(f"  名称: {agent.config.name}")
    print(f"  角色: {agent.config.role}")
    print(f"  模型: {agent.llm.model_name}")
    print()

    # 2. 第一轮对话
    print("=" * 60)
    print("第一轮对话")
    print("=" * 60)

    message1 = Message(
        sender="user",
        sender_name="用户",
        content="你好，我想了解一下城市生活垃圾的主要处理方法有哪些？",
        msg_type=MessageType.REQUEST
    )

    print(f"用户: {message1.content}")
    print()

    response1 = await agent.run(message1)

    print(f"Agent: {response1.content}")
    print()

    # 3. 第二轮对话（测试记忆）
    print("=" * 60)
    print("第二轮对话（测试记忆）")
    print("=" * 60)

    message2 = Message(
        sender="user",
        sender_name="用户",
        content="那其中哪种方法最环保？",
        msg_type=MessageType.REQUEST
    )

    print(f"用户: {message2.content}")
    print()

    response2 = await agent.run(message2)

    print(f"Agent: {response2.content}")
    print()

    # 4. 查看Agent状态
    print("=" * 60)
    print("Agent状态")
    print("=" * 60)

    state = agent.get_state()
    print(f"Agent ID: {state['agent_id']}")
    print(f"状态: {state['state']}")
    print(f"对话消息数: {state['context_summary']['message_count']}")
    print()

    # 5. 使用任务分析功能
    print("=" * 60)
    print("任务分析示例")
    print("=" * 60)

    task = "为一个10万人口的小城市设计垃圾分类回收系统"
    print(f"任务: {task}")
    print()
    print("分析中...")
    print()

    analysis = await agent.analyze_task(task)

    print("分析结果:")
    print(analysis["analysis"])
    print()


if __name__ == "__main__":
    asyncio.run(main())
