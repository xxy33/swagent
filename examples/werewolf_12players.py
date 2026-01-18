"""
狼人杀游戏 - 12人局使用真实SWAgent智能体

完整使用SWAgent框架：
- BaseAgent作为基类
- AgentConfig配置
- Message消息通信
- 真实LLM推理
"""
import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Optional
import random
import os

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from swagent import BaseAgent, AgentConfig, Message, MessageType
from swagent.llm import LLMConfig


# ============================================================================
# 游戏角色Agent定义
# ============================================================================

class WerewolfGameAgent(BaseAgent):
    """狼人杀游戏Agent基类"""

    def __init__(self, config: AgentConfig, game_state: Dict):
        super().__init__(config)
        self.game_state = game_state
        self.role_type = "unknown"

    async def process(self, message: Message) -> Message:
        """处理消息 - 必须实现的抽象方法"""
        # 使用chat方法处理
        response_text = await self.chat(message.content, use_history=False)

        return Message(
            sender=self.agent_id,
            sender_name=self.config.name,
            receiver=message.sender,
            receiver_name=message.sender_name,
            content=response_text,
            msg_type=MessageType.RESPONSE
        )

    async def discuss(self, context: str, other_players: List[str]) -> str:
        """讨论发言"""
        prompt = f"{context}\n\n你怀疑谁是狼人？请简短发言（1-2句话）："
        response = await self.chat(prompt, use_history=False)
        return response.strip()


class WerewolfAgent(WerewolfGameAgent):
    """狼人Agent"""

    def __init__(self, name: str, llm_config: LLMConfig, game_state: Dict, allies: List[str]):
        config = AgentConfig(
            name=name,
            role="狼人",
            description=f"狼人，盟友：{', '.join(allies)}",
            system_prompt=f"""你是狼人杀游戏中的狼人{name}。
你的目标是隐藏身份，白天伪装成好人，误导其他玩家。
你的狼人盟友是：{', '.join(allies)}
你需要保护他们，同时消灭好人阵营。
回答要简洁，1-2句话。""",
            llm_config=llm_config,
            temperature=0.8
        )
        super().__init__(config, game_state)
        self.role_type = "werewolf"
        self.allies = allies


class SeerAgent(WerewolfGameAgent):
    """预言家Agent"""

    def __init__(self, name: str, llm_config: LLMConfig, game_state: Dict):
        config = AgentConfig(
            name=name,
            role="预言家",
            description="预言家，可查验身份",
            system_prompt=f"""你是狼人杀游戏中的预言家{name}。
你每晚可以查验一名玩家的身份。
你的目标是用查验信息引导好人阵营找出狼人。
回答要简洁，1-2句话。""",
            llm_config=llm_config,
            temperature=0.8
        )
        super().__init__(config, game_state)
        self.role_type = "seer"
        self.checked_players = {}

    def check_player(self, player_name: str, is_werewolf: bool) -> str:
        """查验玩家"""
        result = "狼人" if is_werewolf else "好人"
        self.checked_players[player_name] = result
        return result


class WitchAgent(WerewolfGameAgent):
    """女巫Agent"""

    def __init__(self, name: str, llm_config: LLMConfig, game_state: Dict):
        config = AgentConfig(
            name=name,
            role="女巫",
            description="女巫，拥有解药和毒药",
            system_prompt=f"""你是狼人杀游戏中的女巫{name}。
你拥有一瓶解药和一瓶毒药（各用一次）。
要谨慎使用药物，帮助好人阵营获胜。
回答要简洁，1-2句话。""",
            llm_config=llm_config,
            temperature=0.8
        )
        super().__init__(config, game_state)
        self.role_type = "witch"
        self.has_antidote = True
        self.has_poison = True


class HunterAgent(WerewolfGameAgent):
    """猎人Agent"""

    def __init__(self, name: str, llm_config: LLMConfig, game_state: Dict):
        config = AgentConfig(
            name=name,
            role="猎人",
            description="猎人，被淘汰时可开枪",
            system_prompt=f"""你是狼人杀游戏中的猎人{name}。
你被淘汰时可以开枪带走一名玩家。
要保护好自己，在关键时刻发挥作用。
回答要简洁，1-2句话。""",
            llm_config=llm_config,
            temperature=0.8
        )
        super().__init__(config, game_state)
        self.role_type = "hunter"
        self.can_shoot = True


class VillagerAgent(WerewolfGameAgent):
    """村民Agent"""

    def __init__(self, name: str, llm_config: LLMConfig, game_state: Dict):
        config = AgentConfig(
            name=name,
            role="村民",
            description="普通村民",
            system_prompt=f"""你是狼人杀游戏中的村民{name}。
你没有特殊能力，但要通过推理找出狼人。
仔细观察每个人的发言，投票淘汰狼人。
回答要简洁，1-2句话。""",
            llm_config=llm_config,
            temperature=0.8
        )
        super().__init__(config, game_state)
        self.role_type = "villager"


class GuardAgent(WerewolfGameAgent):
    """守卫Agent"""

    def __init__(self, name: str, llm_config: LLMConfig, game_state: Dict):
        config = AgentConfig(
            name=name,
            role="守卫",
            description="守卫，每晚可以守护一名玩家",
            system_prompt=f"""你是狼人杀游戏中的守卫{name}。
你每晚可以守护一名玩家，阻止其被狼人击杀。
要谨慎选择守护目标，保护关键角色。
回答要简洁，1-2句话。""",
            llm_config=llm_config,
            temperature=0.8
        )
        super().__init__(config, game_state)
        self.role_type = "guard"
        self.last_guarded = None


# ============================================================================
# 游戏管理器
# ============================================================================

class WerewolfGame12Players:
    """12人局狼人杀游戏管理器"""

    def __init__(self, llm_config: LLMConfig):
        """
        初始化游戏

        Args:
            llm_config: LLM配置
        """
        self.llm_config = llm_config

        self.agents: Dict[str, WerewolfGameAgent] = {}
        self.alive_players: List[str] = []
        self.dead_players: List[str] = []
        self.werewolves: List[str] = []
        self.day = 0

        self.game_state = {
            'alive_players': self.alive_players,
            'dead_players': self.dead_players,
            'werewolves': self.werewolves,
            'day': 0
        }

    def _get_role_icon(self, role_type: str) -> str:
        """获取角色图标"""
        icons = {
            'werewolf': '🐺',
            'seer': '👁️',
            'witch': '💊',
            'hunter': '🔫',
            'guard': '🛡️',
            'villager': '👤'
        }
        return icons.get(role_type, '👤')

    def setup_game(self):
        """设置12人局游戏"""
        print("\n" + "="*70)
        print("🎮 狼人杀游戏 - 12人标准局（SWAgent智能体版）")
        print("="*70)
        print("   运行模式：🧠 真实LLM推理")

        # 12人局标准配置
        roles = [
            'werewolf', 'werewolf', 'werewolf', 'werewolf',  # 4狼
            'seer',      # 1预言家
            'witch',     # 1女巫
            'hunter',    # 1猎人
            'guard',     # 1守卫
            'villager', 'villager', 'villager', 'villager'  # 4村民
        ]

        random.shuffle(roles)
        player_names = [f"玩家{i+1}" for i in range(12)]

        # 收集狼人名单
        werewolf_names = []
        for name, role in zip(player_names, roles):
            if role == 'werewolf':
                werewolf_names.append(name)
                self.werewolves.append(name)

        # 创建Agent
        print("\n🔧 初始化智能体...")
        for name, role in zip(player_names, roles):
            if role == 'werewolf':
                agent = WerewolfAgent(
                    name, self.llm_config, self.game_state,
                    [w for w in werewolf_names if w != name]
                )
            elif role == 'seer':
                agent = SeerAgent(name, self.llm_config, self.game_state)
            elif role == 'witch':
                agent = WitchAgent(name, self.llm_config, self.game_state)
            elif role == 'hunter':
                agent = HunterAgent(name, self.llm_config, self.game_state)
            elif role == 'guard':
                agent = GuardAgent(name, self.llm_config, self.game_state)
            else:
                agent = VillagerAgent(name, self.llm_config, self.game_state)

            self.agents[name] = agent
            self.alive_players.append(name)

        # 显示配置
        print(f"\n📋 游戏配置：")
        print(f"   总人数：12人")
        print(f"   🐺 狼人：4人")
        print(f"   👁️  预言家：1人")
        print(f"   💊 女巫：1人")
        print(f"   🔫 猎人：1人")
        print(f"   🛡️  守卫：1人")
        print(f"   👤 村民：4人")

        print(f"\n🎭 角色分配：")
        for name, agent in self.agents.items():
            icon = self._get_role_icon(agent.role_type)
            print(f"   {icon} {name}: {agent.config.role}")

    async def night_phase(self):
        """夜晚阶段"""
        print("\n" + "="*70)
        print(f"🌙 第 {self.day} 夜")
        print("="*70)

        deaths = []
        guarded_player = None

        # 1. 守卫守护
        print("\n🛡️  守卫行动...")
        guard = next((a for a in self.agents.values()
                     if a.role_type == 'guard' and a.config.name in self.alive_players), None)

        if guard:
            guardable = [p for p in self.alive_players if p != guard.last_guarded]
            if guardable:
                guarded_player = random.choice(guardable)
                guard.last_guarded = guarded_player
                print(f"   守卫守护了一名玩家")

        # 2. 狼人击杀
        print("\n🐺 狼人行动...")
        alive_wolves = [n for n in self.alive_players if n in self.werewolves]

        if alive_wolves:
            targets = [p for p in self.alive_players if p not in self.werewolves]
            if targets:
                victim = random.choice(targets)
                print(f"   狼人团队击杀：{victim}")
                # 如果被守卫守护，则不会死亡
                if guarded_player != victim:
                    deaths.append((victim, "被狼人击杀"))
                else:
                    print(f"   但{victim}被守卫守护，幸免于难！")

        # 3. 预言家查验
        print("\n🔮 预言家查验...")
        seer = next((a for a in self.agents.values()
                    if a.role_type == 'seer' and a.config.name in self.alive_players), None)

        if seer:
            checkable = [p for p in self.alive_players
                        if p != seer.config.name and p not in seer.checked_players]
            if checkable:
                target = random.choice(checkable)
                is_wolf = target in self.werewolves
                result = seer.check_player(target, is_wolf)
                print(f"   {seer.config.name} 查验 {target}：{result}")

        # 4. 女巫
        print("\n💊 女巫行动...")
        witch = next((a for a in self.agents.values()
                     if a.role_type == 'witch' and a.config.name in self.alive_players), None)

        saved = False
        if witch and deaths and random.random() < 0.3:
            if witch.has_antidote:
                victim, _ = deaths[0]
                print(f"   女巫用解药救了 {victim}")
                deaths = deaths[1:]  # 移除被救的
                witch.has_antidote = False
                saved = True

        # 结算死亡
        print("\n☠️  夜晚结束...")
        if deaths:
            for player, reason in deaths:
                if player in self.alive_players:
                    self.alive_players.remove(player)
                    self.dead_players.append(player)
                    agent = self.agents[player]
                    icon = self._get_role_icon(agent.role_type)
                    print(f"   {icon} {player} ({agent.config.role}) {reason}")
        else:
            print("   昨晚平安夜")

        await asyncio.sleep(0.5)

    async def day_phase(self):
        """白天阶段"""
        print("\n" + "="*70)
        print(f"☀️  第 {self.day} 天")
        print("="*70)

        alive_wolves = len([p for p in self.alive_players if p in self.werewolves])
        alive_good = len([p for p in self.alive_players if p not in self.werewolves])

        print(f"\n📊 当前状态：")
        print(f"   存活（{len(self.alive_players)}人）：{', '.join(self.alive_players)}")
        print(f"   阵营：🐺 {alive_wolves} vs 👥 {alive_good}")

        # 讨论环节
        print("\n💬 讨论环节...")
        print("-" * 70)

        speakers = self.alive_players.copy()
        random.shuffle(speakers)

        for i, name in enumerate(speakers, 1):
            agent = self.agents[name]
            others = [p for p in self.alive_players if p != name]

            context = f"第{self.day}天讨论，存活{len(self.alive_players)}人"

            try:
                statement = await agent.discuss(context, others)
                icon = self._get_role_icon(agent.role_type)
                print(f"\n   [{i}/{len(speakers)}] {icon} {name}:")
                print(f"        「{statement}」")
            except Exception as e:
                print(f"   [{i}/{len(speakers)}] {name}: [思考中...]")

            if i % 3 == 0:
                await asyncio.sleep(0.3)

        # 投票环节
        print("\n" + "-"*70)
        print("🗳️  投票环节")
        print("-" * 70)

        votes = {}
        for name in self.alive_players:
            agent = self.agents[name]
            candidates = [p for p in self.alive_players if p != name]

            if not candidates:
                continue

            # 投票策略
            if agent.role_type == 'werewolf':
                non_wolves = [p for p in candidates if p not in self.werewolves]
                target = random.choice(non_wolves if non_wolves else candidates)
            elif agent.role_type == 'seer' and hasattr(agent, 'checked_players'):
                known_wolves = [p for p in candidates
                              if agent.checked_players.get(p) == '狼人']
                target = random.choice(known_wolves if known_wolves else candidates)
            else:
                target = random.choice(candidates)

            votes[name] = target
            icon = self._get_role_icon(agent.role_type)
            print(f"   {icon} {name} → {target}")

        # 统计投票
        if votes:
            vote_counts = {}
            for t in votes.values():
                vote_counts[t] = vote_counts.get(t, 0) + 1

            max_votes = max(vote_counts.values())
            candidates = [p for p, v in vote_counts.items() if v == max_votes]

            print(f"\n📊 投票结果：")
            for p, c in sorted(vote_counts.items(), key=lambda x: -x[1])[:5]:
                icon = self._get_role_icon(self.agents[p].role_type)
                print(f"   {icon} {p}: {c}票 {'█' * c}")

            eliminated = random.choice(candidates)
            agent = self.agents[eliminated]
            icon = self._get_role_icon(agent.role_type)

            print(f"\n🚫 {icon} {eliminated} ({agent.config.role}) 被淘汰！")

            self.alive_players.remove(eliminated)
            self.dead_players.append(eliminated)

            # 猎人开枪
            if agent.role_type == 'hunter' and agent.can_shoot:
                print(f"\n🔫 {eliminated} 是猎人！开枪...")
                await asyncio.sleep(0.5)

                if self.alive_players:
                    target = random.choice(self.alive_players)
                    print(f"   猎人带走了 {target}！")
                    self.alive_players.remove(target)
                    self.dead_players.append(target)

    def check_game_over(self) -> Optional[str]:
        """检查游戏结束"""
        wolves = [p for p in self.alive_players if p in self.werewolves]
        good = [p for p in self.alive_players if p not in self.werewolves]

        if not wolves:
            return "good"
        if len(good) <= len(wolves):
            return "werewolf"
        return None

    async def run_game(self, max_days: int = 4):
        """运行游戏"""
        print("\n" + "="*70)
        print("🎬 游戏开始！")
        print("="*70)

        await asyncio.sleep(1)

        for day in range(1, max_days + 1):
            self.day = day
            self.game_state['day'] = day

            await self.night_phase()

            winner = self.check_game_over()
            if winner:
                break

            await self.day_phase()

            winner = self.check_game_over()
            if winner:
                break

            if day < max_days:
                print(f"\n💤 第{day}天结束...")
                await asyncio.sleep(1)

        # 显示结果
        print("\n" + "="*70)
        print("🏁 游戏结束！")
        print("="*70)

        if winner == "good":
            print("\n🎉 好人阵营胜利！")
        elif winner == "werewolf":
            print("\n🐺 狼人阵营胜利！")

        print(f"\n📊 最终状态：")
        print(f"   存活：{', '.join(self.alive_players)}")
        print(f"   淘汰：{', '.join(self.dead_players)}")

        print(f"\n🎭 角色揭晓：")
        for name in self.alive_players:
            agent = self.agents[name]
            icon = self._get_role_icon(agent.role_type)
            camp = "狼人" if name in self.werewolves else "好人"
            print(f"   ✓ {icon} {name}: {agent.config.role} ({camp})")

        for name in self.dead_players:
            agent = self.agents[name]
            icon = self._get_role_icon(agent.role_type)
            camp = "狼人" if name in self.werewolves else "好人"
            print(f"   ✗ {icon} {name}: {agent.config.role} ({camp})")


# ============================================================================
# 主函数
# ============================================================================

async def main():
    """主函数"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "狼人杀游戏 - 12人标准局" + " "*18 + "║")
    print("║" + " "*13 + "基于SWAgent智能体框架" + " "*19 + "║")
    print("╚" + "="*68 + "╝")

    # 加载环境变量
    from dotenv import load_dotenv
    load_dotenv()

    # 配置真实LLM
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("\n❌ 错误：需要设置OPENAI_API_KEY")
        print("💡 提示：在.env文件中设置 OPENAI_API_KEY=your_key")
        print("或运行：export OPENAI_API_KEY=your_key")
        return

    llm_config = LLMConfig(
        provider="openai",
        model="gpt-3.5-turbo",
        api_key=api_key,
        base_url=os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
        temperature=0.8
    )

    # 创建游戏
    game = WerewolfGame12Players(llm_config)
    game.setup_game()

    await asyncio.sleep(1.5)

    try:
        await game.run_game(max_days=5)
    except KeyboardInterrupt:
        print("\n\n⚠️  游戏中断")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()

    print("\n✨ 演示结束！\n")


if __name__ == "__main__":
    asyncio.run(main())
