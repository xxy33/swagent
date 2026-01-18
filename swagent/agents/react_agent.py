"""
ReAct Agent
基于ReAct（Reasoning and Acting）模式的Agent
专门用于判断多Agent辩论何时应该终结
"""
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from swagent.core.base_agent import BaseAgent, AgentConfig
from swagent.core.message import Message, MessageType
from swagent.utils.logger import get_logger
from swagent.utils.config import get_config


logger = get_logger(__name__)


class DebateStatus(Enum):
    """辩论状态"""
    CONTINUE = "continue"           # 继续讨论
    CONSENSUS = "consensus"         # 达成共识
    DIVERGENCE = "divergence"       # 分歧过大，需要介入
    TIMEOUT = "timeout"             # 超时，强制终止
    SUFFICIENT = "sufficient"       # 信息充分，可以终止


@dataclass
class ThoughtResult:
    """思考结果"""
    reasoning: str                  # 推理过程
    observation: str                # 观察结果
    decision: DebateStatus          # 决策
    confidence: float               # 置信度 (0-1)
    reason: str                     # 决策理由
    suggestions: List[str] = None   # 建议

    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []


class ReActAgent(BaseAgent):
    """
    ReAct Agent

    使用ReAct模式（Reasoning and Acting）进行推理和决策
    主要用于：
    1. 监控多Agent辩论过程
    2. 判断何时终止讨论
    3. 评估讨论质量和共识度
    4. 提供终止建议
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        初始化ReAct Agent

        Args:
            config: Agent配置，如果为None则从配置文件加载
        """
        if config is None:
            config = self._load_react_config()

        super().__init__(config)

        # ReAct特定配置
        self.max_iterations = config.max_iterations
        self.confidence_threshold = 0.7  # 决策置信度阈值

    @staticmethod
    def _load_react_config() -> AgentConfig:
        """从配置文件加载ReAct Agent配置"""
        cfg = get_config()

        return AgentConfig(
            name='ReAct判断Agent',
            role='辩论仲裁者',
            description='负责监控多Agent辩论，判断何时终止讨论，评估共识程度',
            model='gpt-4',
            temperature=0.3,  # 较低温度以获得更稳定的判断
            max_tokens=2048,
            max_iterations=5
        )

    @property
    def system_prompt(self) -> str:
        """ReAct Agent的系统提示"""
        return """你是一个专业的辩论仲裁者Agent，使用ReAct（推理-行动）模式进行判断。

你的职责：
1. 观察多Agent辩论的进展
2. 分析讨论的质量、深度和共识程度
3. 判断何时应该终止讨论
4. 提供清晰的决策理由

判断标准：
- **达成共识(CONSENSUS)**: 各方观点趋于一致，没有重大分歧
- **信息充分(SUFFICIENT)**: 关键信息已充分讨论，继续讨论收益递减
- **分歧过大(DIVERGENCE)**: 观点差异太大，需要外部介入或重新框架
- **继续讨论(CONTINUE)**: 还有价值的讨论空间，应继续
- **超时(TIMEOUT)**: 讨论轮次过多，应强制终止

你的思考过程：
1. **Thought（思考）**: 分析当前讨论状态
2. **Observation（观察）**: 总结关键信息和模式
3. **Action（行动）**: 做出决策并给出理由

请以结构化、客观的方式进行判断。"""

    async def process(self, message: Message) -> Message:
        """
        处理消息

        Args:
            message: 输入消息

        Returns:
            响应消息
        """
        try:
            logger.debug(f"ReActAgent开始处理消息 - {message.content[:50]}...")

            # 使用LLM生成响应
            response_content = await self.chat(
                user_message=message.content,
                use_history=True
            )

            # 创建响应消息
            response = Message(
                sender=self.agent_id,
                sender_name=self.config.name,
                receiver=message.sender,
                receiver_name=message.sender_name,
                content=response_content,
                msg_type=MessageType.RESPONSE,
                parent_id=message.id,
                thread_id=message.thread_id or message.id
            )

            logger.debug(f"ReActAgent处理完成 - 响应长度: {len(response_content)}")

            return response

        except Exception as e:
            logger.error(f"ReActAgent处理出错: {str(e)}", exc_info=True)
            raise

    async def judge_debate_status(
        self,
        debate_history: List[Dict[str, str]],
        current_round: int,
        max_rounds: int = 10
    ) -> ThoughtResult:
        """
        判断辩论状态（核心功能）

        Args:
            debate_history: 辩论历史，格式为 [{"agent": "Agent1", "content": "..."}]
            current_round: 当前轮次
            max_rounds: 最大轮次

        Returns:
            ThoughtResult对象，包含判断结果
        """
        logger.info(f"开始判断辩论状态 - 当前轮次: {current_round}/{max_rounds}")

        # 格式化辩论历史
        debate_text = self._format_debate_history(debate_history)

        # 构建判断提示
        prompt = f"""请使用ReAct模式分析以下辩论，并判断是否应该终止讨论。

当前状态:
- 当前轮次: {current_round}/{max_rounds}
- 参与者数量: {len(set(msg['agent'] for msg in debate_history))}
- 总发言次数: {len(debate_history)}

辩论历史:
{debate_text}

请按以下格式输出:

**Thought（思考）**:
[分析当前讨论的状态，包括：观点是否趋同、信息是否充分、是否有新观点等]

**Observation（观察）**:
[总结关键观察：各方观点、共识点、分歧点、讨论深度等]

**Action（决策）**:
状态: [CONTINUE/CONSENSUS/SUFFICIENT/DIVERGENCE/TIMEOUT中选一个]
置信度: [0.0-1.0之间的数字]
理由: [详细说明做出此决策的理由]
建议: [对后续行动的建议，用|分隔多个建议]

请严格按照以上格式输出。"""

        # 调用LLM进行判断
        response = await self.chat(prompt, use_history=False)

        # 解析响应
        result = self._parse_judgment_response(response)

        logger.info(f"辩论判断完成 - 状态: {result.decision.value}, 置信度: {result.confidence}")

        return result

    def _format_debate_history(self, debate_history: List[Dict[str, str]]) -> str:
        """
        格式化辩论历史

        Args:
            debate_history: 辩论历史

        Returns:
            格式化后的文本
        """
        formatted = []
        for i, msg in enumerate(debate_history, 1):
            agent = msg.get('agent', 'Unknown')
            content = msg.get('content', '')
            formatted.append(f"[轮次{i}] {agent}: {content}")

        return "\n".join(formatted)

    def _parse_judgment_response(self, response: str) -> ThoughtResult:
        """
        解析LLM的判断响应

        Args:
            response: LLM响应文本

        Returns:
            ThoughtResult对象
        """
        # 提取各个部分
        reasoning = self._extract_section(response, "Thought", "Observation")
        observation = self._extract_section(response, "Observation", "Action")
        action_text = self._extract_section(response, "Action", None)

        # 解析Action部分
        decision = DebateStatus.CONTINUE
        confidence = 0.5
        reason = ""
        suggestions = []

        if action_text:
            # 提取状态
            if "CONSENSUS" in action_text.upper():
                decision = DebateStatus.CONSENSUS
            elif "SUFFICIENT" in action_text.upper():
                decision = DebateStatus.SUFFICIENT
            elif "DIVERGENCE" in action_text.upper():
                decision = DebateStatus.DIVERGENCE
            elif "TIMEOUT" in action_text.upper():
                decision = DebateStatus.TIMEOUT
            else:
                decision = DebateStatus.CONTINUE

            # 提取置信度
            import re
            confidence_match = re.search(r'置信度[:：]\s*(0?\.\d+|1\.0|[01])', action_text)
            if confidence_match:
                try:
                    confidence = float(confidence_match.group(1))
                except ValueError:
                    confidence = 0.5

            # 提取理由
            reason_match = re.search(r'理由[:：]\s*(.+?)(?=\n建议[:：]|$)', action_text, re.DOTALL)
            if reason_match:
                reason = reason_match.group(1).strip()

            # 提取建议
            suggestions_match = re.search(r'建议[:：]\s*(.+)', action_text, re.DOTALL)
            if suggestions_match:
                suggestions_text = suggestions_match.group(1).strip()
                suggestions = [s.strip() for s in suggestions_text.split('|') if s.strip()]

        return ThoughtResult(
            reasoning=reasoning.strip(),
            observation=observation.strip(),
            decision=decision,
            confidence=confidence,
            reason=reason,
            suggestions=suggestions
        )

    def _extract_section(self, text: str, start_marker: str, end_marker: Optional[str]) -> str:
        """
        提取文本中的某个section

        Args:
            text: 原始文本
            start_marker: 起始标记
            end_marker: 结束标记，None表示到文本末尾

        Returns:
            提取的文本
        """
        import re

        # 查找起始位置
        start_pattern = rf'\*\*{start_marker}[^*]*\*\*'
        start_match = re.search(start_pattern, text, re.IGNORECASE)

        if not start_match:
            return ""

        start_pos = start_match.end()

        # 查找结束位置
        if end_marker:
            end_pattern = rf'\*\*{end_marker}[^*]*\*\*'
            end_match = re.search(end_pattern, text[start_pos:], re.IGNORECASE)
            if end_match:
                end_pos = start_pos + end_match.start()
            else:
                end_pos = len(text)
        else:
            end_pos = len(text)

        return text[start_pos:end_pos].strip()

    async def should_terminate_debate(
        self,
        debate_history: List[Dict[str, str]],
        current_round: int,
        max_rounds: int = 10,
        min_confidence: float = 0.7
    ) -> tuple[bool, ThoughtResult]:
        """
        判断是否应该终止辩论（简化接口）

        Args:
            debate_history: 辩论历史
            current_round: 当前轮次
            max_rounds: 最大轮次
            min_confidence: 最小置信度阈值

        Returns:
            (是否终止, 判断结果)
        """
        result = await self.judge_debate_status(debate_history, current_round, max_rounds)

        # 判断是否应该终止
        should_stop = (
            result.decision != DebateStatus.CONTINUE and
            result.confidence >= min_confidence
        )

        return should_stop, result

    async def analyze_consensus(
        self,
        debate_history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        分析辩论中的共识程度

        Args:
            debate_history: 辩论历史

        Returns:
            共识分析结果
        """
        debate_text = self._format_debate_history(debate_history)

        prompt = f"""请分析以下辩论中的共识程度：

{debate_text}

请输出：
1. 共识点（各方一致同意的观点）
2. 分歧点（存在争议的观点）
3. 共识度评分（0-10分）
4. 主要观点总结"""

        response = await self.chat(prompt, use_history=False)

        return {
            "analysis": response,
            "debate_rounds": len(debate_history)
        }

    @classmethod
    def create(cls, name: Optional[str] = None) -> 'ReActAgent':
        """
        快速创建ReAct Agent

        Args:
            name: 自定义名称

        Returns:
            ReActAgent实例
        """
        config = cls._load_react_config()

        if name:
            config.name = name

        return cls(config)
