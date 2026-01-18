"""
工作流模块
提供预定义的工作流模板，用于常见任务场景
"""
from .base_workflow import (
    BaseWorkflow,
    WorkflowStep,
    WorkflowContext,
    WorkflowResult,
    StepStatus
)
from .research_workflow import ResearchWorkflow
from .report_workflow import ReportWorkflow
from .analysis_workflow import DataAnalysisWorkflow
from .coding_workflow import CodingWorkflow
from .workflow_manager import WorkflowManager

__all__ = [
    'BaseWorkflow',
    'WorkflowStep',
    'WorkflowContext',
    'WorkflowResult',
    'StepStatus',
    'ResearchWorkflow',
    'ReportWorkflow',
    'DataAnalysisWorkflow',
    'CodingWorkflow',
    'WorkflowManager',
]
