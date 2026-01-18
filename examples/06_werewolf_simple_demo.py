"""
狼人杀游戏 - 多Agent交互简化演示

这个版本简化了游戏规则，展示多个Agent之间的推理和投票机制。
"""
import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Optional
import random

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from swagent import BaseAgent, AgentConfig, Message, MessageType
from swagent.llm import OpenAIClient, LLMConfig


# ============================================================================
# 游戏角色Agent定义
# ============================================================================

class WerewolfAgent(BaseAgent):
    """狼人Agent"""

    def __init__(self, name: str, llm_config: LLMConfig, game_state: Dict):
        config = AgentConfig(
            name=name,
            role="狼人",
            description="知道同伴身份的狼人，目标是隐藏身份并消灭好人",
            system_prompt=f"""你是狼人杀游戏中的狼人{name}。
你的目标是隐藏身份，在白天讨论时误导其他玩家。
回答要简洁，1-2句话。""",
            llm_config=llm_config,
            temperature=0.8
        )
        super().__init__(config)
        self.game_state = game_state
        self.role_type = "werewolf"

    async def process(self, message: Message) -> Message:
        """处理消息"""
        response_text = await self.chat(message.content)
        return Message(
            sender=self.agent_id,
            sender_name=self.config.name,
            receiver=message.sender,
            receiver_name=message.sender_name,
            content=response_text,
            msg_type=MessageType.RESPONSE
        )


class VillagerAgent(BaseAgent):
    """村民Agent"""

    def __init__(self, name: str, llm_config: LLMConfig, game_state: Dict):
        config = AgentConfig(
            name=name,
            role="村民",
            description="普通村民，通过推理找出狼人",
            system_prompt=f"""你是狼人杀游戏中的村民{name}。
你是好人阵营，通过观察和推理找出狼人。
回答要简洁，1-2句话。""",
            llm_config=llm_config,
            temperature=0.8
        )
        super().__init__(config)
        self.game_state = game_state
        self.role_type = "villager"

    async def process(self, message: Message) -> Message:
        """处理消息"""
        response_text = await self.chat(message.content)
        return Message(
            sender=self.agent_id,
            sender_name=self.config.name,
            receiver=message.sender,
            receiver_name=message.sender_name,
            content=response_text,
            msg_type=MessageType.RESPONSE
        )


class SeerAgent(BaseAgent):
    """预言家Agent"""

    def __init__(self, name: str, llm_config: LLMConfig, game_state: Dict):
        config = AgentConfig(
            name=name,
            role="预言家",
            description="每晚可以查验一个玩家身份的预言家",
            system_prompt=f"""你是狼人杀游戏中的预言家{name}。
你拥有查验身份的能力，可以引导好人阵营。
回答要简洁，1-2句话。""",
            llm_config=llm_config,
            temperature=0.8
        )
        super().__init__(config)
        self.game_state = game_state
        self.role_type = "seer"
        self.checked_players = {}

    def check_player(self, player_name: str) -> str:
        """查验玩家身份"""
        if player_name in self.game_state['werewolves']:
            result = "狼人"
        else:
            result = "好人"
        self.checked_players[player_name] = result
        return result

    async def process(self, message: Message) -> Message:
        """处理消息"""
        response_text = await self.chat(message.content)
        return Message(
            sender=self.agent_id,
            sender_name=self.config.name,
            receiver=message.sender,
            receiver_name=message.sender_name,
            content=response_text,
            msg_type=MessageType.RESPONSE
        )


# ============================================================================
# 游戏管理器
# ============================================================================

class WerewolfGame:
    """狼人杀游戏管理器"""

    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
        self.game_state = {
            'alive_players': [],
            'dead_players': [],
            'werewolves': [],
            'last_death': None,
            'day': 0
        }
        self.agents: Dict[str, BaseAgent] = {}

    def setup_game(self):
        """设置游戏（4人简化版）"""
        print("\n" + "="*60)
        print("🎮 狼人杀游戏初始化（简化版：4人局）")
        print("="*60)

        # 4人局配置：1狼人、1预言家、2村民
        roles = ['werewolf', 'seer', 'villager', 'villager']
        random.shuffle(roles)
        player_names = [f"玩家{i+1}" for i in range(4)]

        # 创建Agent
        for name, role in zip(player_names, roles):
            if role == 'werewolf':
                agent = WerewolfAgent(name, self.llm_config, self.game_state)
                self.game_state['werewolves'].append(name)
            elif role == 'seer':
                agent = SeerAgent(name, self.llm_config, self.game_state)
            else:
                agent = VillagerAgent(name, self.llm_config, self.game_state)

            self.agents[name] = agent
            self.game_state['alive_players'].append(name)

        # 显示角色配置
        print("\n📋 游戏配置：")
        print(f"   总玩家数：4")
        print(f"   狼人：1人")
        print(f"   预言家：1人")
        print(f"   村民：2人")

        print("\n🎭 角色分配（作弊模式 - 仅用于演示）：")
        for name, agent in self.agents.items():
            print(f"   {name}: {agent.config.role}")

    async def night_phase(self):
        """夜晚阶段"""
        print("\n" + "="*60)
        print(f"🌙 第 {self.game_state['day']} 夜")
        print("="*60)

        # 1. 狼人杀人
        print("\n🐺 狼人行动...")
        wolves = [name for name, agent in self.agents.items()
                 if agent.role_type == 'werewolf' and name in self.game_state['alive_players']]

        if wolves:
            targets = [p for p in self.game_state['alive_players'] if p not in wolves]
            if targets:
                kill_target = random.choice(targets)
                print(f"   狼人击杀: {kill_target}")
                self.game_state['wolf_kill'] = kill_target

        # 2. 预言家查验
        print("\n🔮 预言家查验...")
        seer_agent = next((agent for agent in self.agents.values()
                           if agent.role_type == 'seer' and agent.config.name in self.game_state['alive_players']), None)

        if seer_agent:
            checkable = [p for p in self.game_state['alive_players']
                        if p != seer_agent.config.name and p not in seer_agent.checked_players]
            if checkable:
                check_target = random.choice(checkable)
                result = seer_agent.check_player(check_target)
                print(f"   {seer_agent.config.name} 查验 {check_target}: {result}")

        # 3. 结算死亡
        print("\n☠️  夜晚结束...")
        if self.game_state.get('wolf_kill'):
            victim = self.game_state['wolf_kill']
            self.game_state['alive_players'].remove(victim)
            self.game_state['dead_players'].append(victim)
            self.game_state['last_death'] = victim
            print(f"   昨晚死亡：{victim} ({self.agents[victim].config.role})")
        else:
            self.game_state['last_death'] = None
            print("   昨晚平安夜")

        await asyncio.sleep(1)

    async def day_phase(self):
        """白天阶段"""
        print("\n" + "="*60)
        print(f"☀️  第 {self.game_state['day']} 天")
        print("="*60)

        print(f"\n📊 存活玩家：{', '.join(self.game_state['alive_players'])}")

        # 1. 讨论环节
        print("\n💬 讨论环节...")
        context = f"第{self.game_state['day']}天。"
        if self.game_state.get('last_death'):
            context += f"昨晚{self.game_state['last_death']}死亡。"

        for name in self.game_state['alive_players']:
            agent = self.agents[name]
            prompt = f"{context}你怀疑谁是狼人？（1-2句话）"

            try:
                statement = await agent.chat(prompt, use_history=False)
                print(f"\n   {name}（{agent.config.role}）：")
                print(f"   「{statement.strip()}」")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"   {name}: [思考中...]")

        # 2. 投票环节
        print("\n" + "-"*60)
        print("🗳️  投票环节")
        print("-"*60)

        votes = {}
        for name in self.game_state['alive_players']:
            candidates = [p for p in self.game_state['alive_players'] if p != name]
            if candidates:
                vote_target = random.choice(candidates)
                votes[name] = vote_target
                print(f"   {name} → {vote_target}")

        # 3. 统计投票结果
        if votes:
            vote_counts = {}
            for target in votes.values():
                vote_counts[target] = vote_counts.get(target, 0) + 1

            max_votes = max(vote_counts.values())
            eliminated_candidates = [p for p, v in vote_counts.items() if v == max_votes]
            eliminated = random.choice(eliminated_candidates)

            print(f"\n📊 投票统计：")
            for player, count in sorted(vote_counts.items(), key=lambda x: -x[1]):
                print(f"   {player}: {count}票")

            print(f"\n🚫 {eliminated} ({self.agents[eliminated].config.role}) 被淘汰！")
            self.game_state['alive_players'].remove(eliminated)
            self.game_state['dead_players'].append(eliminated)

        await asyncio.sleep(1)

    def check_game_over(self) -> Optional[str]:
        """检查游戏是否结束"""
        alive_wolves = [name for name in self.game_state['alive_players']
                       if name in self.game_state['werewolves']]
        alive_good = [name for name in self.game_state['alive_players']
                     if name not in self.game_state['werewolves']]

        if not alive_wolves:
            return "good"
        if len(alive_good) <= len(alive_wolves):
            return "werewolf"
        return None

    async def run_game(self):
        """运行游戏"""
        print("\n🎬 游戏开始！\n")

        for day in range(1, 4):  # 最多3天
            self.game_state['day'] = day

            # 夜晚阶段
            await self.night_phase()

            # 检查游戏是否结束
            winner = self.check_game_over()
            if winner:
                break

            # 白天阶段
            await self.day_phase()

            # 检查游戏是否结束
            winner = self.check_game_over()
            if winner:
                break

        # 游戏结束
        print("\n" + "="*60)
        print("🏁 游戏结束！")
        print("="*60)

        if winner == "good":
            print("\n🎉 好人阵营胜利！")
        elif winner == "werewolf":
            print("\n🐺 狼人阵营胜利！")
        else:
            print("\n⏱️  游戏达到最大回合数")

        print(f"\n📊 最终结果：")
        print(f"   存活：{', '.join(self.game_state['alive_players'])}")
        print(f"   死亡：{', '.join(self.game_state['dead_players'])}")

        print(f"\n🎭 角色揭晓：")
        for name, agent in self.agents.items():
            status = "存活" if name in self.game_state['alive_players'] else "死亡"
            print(f"   {name}: {agent.config.role} ({status})")


# ============================================================================
# 主函数
# ============================================================================

async def main():
    """主函数"""
    print("\n")
    print("╔" + "═"*58 + "╗")
    print("║" + " "*10 + "狼人杀游戏 - 多Agent交互演示" + " "*12 + "║")
    print("╚" + "═"*58 + "╝")

    print("\n⚙️  配置LLM...")

    import os
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv('OPENAI_API_KEY')
    base_url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')

    if not api_key:
        print("❌ 错误：未找到OPENAI_API_KEY环境变量")
        print("请在.env文件中设置OPENAI_API_KEY")
        return

    llm_config = LLMConfig(
        provider="openai",
        model="gpt-3.5-turbo",
        api_key=api_key,
        base_url=base_url,
        temperature=0.8
    )

    print("✓ LLM配置完成")

    # 创建并运行游戏
    game = WerewolfGame(llm_config)
    game.setup_game()

    print("\n" + "="*60)
    print("🚀 游戏开始...")
    await asyncio.sleep(1)

    try:
        await game.run_game()
    except KeyboardInterrupt:
        print("\n\n⚠️  游戏被中断")
    except Exception as e:
        print(f"\n❌ 游戏出错: {str(e)}")
        import traceback
        traceback.print_exc()

    print("\n✨ 演示结束！")


if __name__ == "__main__":
    asyncio.run(main())
