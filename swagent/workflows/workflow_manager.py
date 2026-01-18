"""
工作流管理器
提供工作流的注册、查询和执行管理
"""
from typing import Dict, Type, Optional, List
from .base_workflow import BaseWorkflow, WorkflowResult
from .research_workflow import ResearchWorkflow
from .report_workflow import ReportWorkflow
from .analysis_workflow import DataAnalysisWorkflow
from .coding_workflow import CodingWorkflow


class WorkflowManager:
    """
    工作流管理器

    负责注册、管理和执行各种工作流模板
    """

    def __init__(self):
        """初始化工作流管理器"""
        self._workflows: Dict[str, Type[BaseWorkflow]] = {}
        self._register_builtin_workflows()

    def _register_builtin_workflows(self):
        """注册内置工作流"""
        self.register('research', ResearchWorkflow)
        self.register('report', ReportWorkflow)
        self.register('analysis', DataAnalysisWorkflow)
        self.register('coding', CodingWorkflow)

    def register(self, name: str, workflow_class: Type[BaseWorkflow]):
        """
        注册工作流

        Args:
            name: 工作流名称
            workflow_class: 工作流类
        """
        self._workflows[name] = workflow_class

    def get_workflow(self, name: str) -> Optional[BaseWorkflow]:
        """
        获取工作流实例

        Args:
            name: 工作流名称

        Returns:
            工作流实例，如果不存在则返回None
        """
        workflow_class = self._workflows.get(name)
        if workflow_class:
            return workflow_class()
        return None

    def list_workflows(self) -> List[Dict[str, str]]:
        """
        列出所有注册的工作流

        Returns:
            工作流信息列表
        """
        workflows = []
        for name, workflow_class in self._workflows.items():
            instance = workflow_class()
            workflows.append({
                'name': name,
                'title': instance.name,
                'description': instance.description,
                'steps': len(instance.steps)
            })
        return workflows

    async def execute_workflow(
        self,
        name: str,
        initial_context: Optional[Dict] = None,
        stop_on_error: bool = True
    ) -> WorkflowResult:
        """
        执行工作流

        Args:
            name: 工作流名称
            initial_context: 初始上下文
            stop_on_error: 遇到错误时是否停止

        Returns:
            WorkflowResult对象

        Raises:
            ValueError: 如果工作流不存在
        """
        workflow = self.get_workflow(name)
        if not workflow:
            raise ValueError(f"Workflow '{name}' not found")

        result = await workflow.execute(initial_context, stop_on_error)
        return result

    def get_workflow_steps(self, name: str) -> Optional[List[Dict[str, str]]]:
        """
        获取工作流的步骤信息

        Args:
            name: 工作流名称

        Returns:
            步骤信息列表
        """
        workflow = self.get_workflow(name)
        if not workflow:
            return None

        steps = []
        for step in workflow.steps:
            steps.append({
                'name': step.name,
                'description': step.description,
                'required_inputs': step.required_inputs,
                'optional_inputs': step.optional_inputs,
                'outputs': step.outputs
            })
        return steps

    def is_workflow_registered(self, name: str) -> bool:
        """
        检查工作流是否已注册

        Args:
            name: 工作流名称

        Returns:
            是否已注册
        """
        return name in self._workflows

    def unregister(self, name: str) -> bool:
        """
        取消注册工作流

        Args:
            name: 工作流名称

        Returns:
            是否成功取消注册
        """
        if name in self._workflows:
            del self._workflows[name]
            return True
        return False

    def get_workflow_by_purpose(self, purpose: str) -> List[str]:
        """
        根据用途推荐工作流

        Args:
            purpose: 用途描述

        Returns:
            推荐的工作流名称列表
        """
        purpose_lower = purpose.lower()
        recommendations = []

        mappings = {
            'research': ['文献', '研究', '论文', '科研'],
            'report': ['报告', '总结', '评估', '汇报'],
            'analysis': ['分析', '数据', '统计', '可视化'],
            'coding': ['开发', '编程', '代码', 'bug', '功能']
        }

        for workflow_name, keywords in mappings.items():
            if any(keyword in purpose_lower for keyword in keywords):
                recommendations.append(workflow_name)

        return recommendations if recommendations else ['research']  # 默认推荐科研工作流

    def __len__(self) -> int:
        """返回已注册工作流的数量"""
        return len(self._workflows)

    def __contains__(self, name: str) -> bool:
        """检查工作流是否已注册"""
        return name in self._workflows

    def __repr__(self) -> str:
        return f"<WorkflowManager ({len(self)} workflows)>"


# 全局单例
_global_workflow_manager: Optional[WorkflowManager] = None


def get_workflow_manager() -> WorkflowManager:
    """
    获取全局工作流管理器实例

    Returns:
        WorkflowManager实例
    """
    global _global_workflow_manager

    if _global_workflow_manager is None:
        _global_workflow_manager = WorkflowManager()

    return _global_workflow_manager
