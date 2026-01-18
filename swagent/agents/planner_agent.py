"""
规划Agent
负责任务分析、规划和协调
"""
from typing import Optional

from swagent.core.base_agent import BaseAgent, AgentConfig
from swagent.core.message import Message, MessageType
from swagent.utils.logger import get_logger
from swagent.utils.config import get_config


logger = get_logger(__name__)


class PlannerAgent(BaseAgent):
    """
    规划Agent

    负责：
    1. 分析用户需求
    2. 制定执行计划
    3. 协调其他Agent
    4. 提供专业建议
    """

    def __init__(self, config: Optional[AgentConfig] = None):
        """
        初始化规划Agent

        Args:
            config: Agent配置，如果为None则从配置文件加载
        """
        if config is None:
            config = self._load_planner_config()

        super().__init__(config)

    @staticmethod
    def _load_planner_config() -> AgentConfig:
        """从配置文件加载规划Agent配置"""
        cfg = get_config()
        planner_cfg = cfg.get('agents.planner', {})

        return AgentConfig(
            name=planner_cfg.get('name', '规划Agent'),
            role=planner_cfg.get('role', '任务规划师'),
            description=planner_cfg.get('description', '负责分析任务、制定执行计划并协调其他Agent完成工作'),
            model=planner_cfg.get('model', 'gpt-4'),
            temperature=planner_cfg.get('temperature', 0.5),
            max_tokens=planner_cfg.get('max_tokens', 4096)
        )

    @property
    def system_prompt(self) -> str:
        """规划Agent的系统提示"""
        return """你是一个专业的任务规划师Agent，擅长分析问题和制定执行计划。

你的职责包括：
1. 理解用户需求，分析任务目标
2. 将复杂任务分解为可执行的步骤
3. 识别所需的资源和工具
4. 提供清晰、可行的解决方案
5. 在固体废物领域提供专业建议

你的特点：
- 逻辑清晰，思路缜密
- 善于将复杂问题简单化
- 关注实际可操作性
- 对固体废物管理领域有深入了解

请以专业、友好的方式回应用户，提供有价值的见解和建议。"""

    async def process(self, message: Message) -> Message:
        """
        处理消息

        Args:
            message: 输入消息

        Returns:
            响应消息
        """
        try:
            logger.debug(f"PlannerAgent开始处理消息 - {message.content[:50]}...")

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

            logger.debug(f"PlannerAgent处理完成 - 响应长度: {len(response_content)}")

            return response

        except Exception as e:
            logger.error(f"PlannerAgent处理出错: {str(e)}", exc_info=True)
            raise

    async def analyze_task(self, task_description: str) -> dict:
        """
        分析任务

        Args:
            task_description: 任务描述

        Returns:
            任务分析结果
        """
        prompt = f"""请分析以下任务，并提供：
1. 任务目标
2. 主要步骤（分解为3-5个步骤）
3. 所需资源/工具
4. 潜在挑战
5. 建议方案

任务描述：{task_description}

请以结构化的方式回答。"""

        response = await self.chat(prompt, use_history=False)

        return {
            "task": task_description,
            "analysis": response
        }

    async def create_plan(self, goal: str, context: Optional[dict] = None) -> str:
        """
        创建执行计划

        Args:
            goal: 目标描述
            context: 上下文信息

        Returns:
            执行计划
        """
        context_str = ""
        if context:
            context_str = f"\n\n上下文信息：\n{context}"

        prompt = f"""请为以下目标制定详细的执行计划：

目标：{goal}{context_str}

请提供：
1. 总体策略
2. 具体步骤（编号列出）
3. 每步的关键要点
4. 预期成果
5. 风险提示

请确保计划切实可行。"""

        plan = await self.chat(prompt, use_history=False)

        return plan

    @classmethod
    def create(cls, name: Optional[str] = None) -> 'PlannerAgent':
        """
        快速创建规划Agent

        Args:
            name: 自定义名称

        Returns:
            PlannerAgent实例
        """
        config = cls._load_planner_config()

        if name:
            config.name = name

        return cls(config)
