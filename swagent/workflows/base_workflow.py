"""
工作流基础架构
定义工作流的抽象基类和通用组件
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable, Awaitable
from enum import Enum
import asyncio
from datetime import datetime


class StepStatus(Enum):
    """步骤状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowContext:
    """工作流上下文，用于在步骤之间传递数据"""
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any):
        """设置上下文数据"""
        self.data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """获取上下文数据"""
        return self.data.get(key, default)

    def has(self, key: str) -> bool:
        """检查键是否存在"""
        return key in self.data

    def update(self, updates: Dict[str, Any]):
        """批量更新上下文"""
        self.data.update(updates)


@dataclass
class WorkflowStep:
    """工作流步骤"""
    name: str
    description: str
    execute_func: Callable[[WorkflowContext], Awaitable[Dict[str, Any]]]
    required_inputs: List[str] = field(default_factory=list)
    optional_inputs: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3

    @property
    def duration(self) -> Optional[float]:
        """步骤执行时长（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    def validate_inputs(self, context: WorkflowContext) -> bool:
        """验证必需的输入是否存在"""
        for key in self.required_inputs:
            if not context.has(key):
                return False
        return True


@dataclass
class WorkflowResult:
    """工作流执行结果"""
    success: bool
    workflow_name: str
    total_steps: int
    completed_steps: int
    failed_steps: int
    skipped_steps: int
    context: WorkflowContext
    step_results: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def duration(self) -> Optional[float]:
        """工作流总时长（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def completion_rate(self) -> float:
        """完成率"""
        if self.total_steps == 0:
            return 0.0
        return self.completed_steps / self.total_steps

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'success': self.success,
            'workflow_name': self.workflow_name,
            'total_steps': self.total_steps,
            'completed_steps': self.completed_steps,
            'failed_steps': self.failed_steps,
            'skipped_steps': self.skipped_steps,
            'completion_rate': self.completion_rate,
            'duration': self.duration,
            'error': self.error,
            'context_data': self.context.data,
            'step_results': self.step_results
        }


class BaseWorkflow(ABC):
    """工作流基类"""

    def __init__(self, name: str, description: str = ""):
        """
        初始化工作流

        Args:
            name: 工作流名称
            description: 工作流描述
        """
        self.name = name
        self.description = description
        self.steps: List[WorkflowStep] = []
        self.context = WorkflowContext()
        self._setup_steps()

    @abstractmethod
    def _setup_steps(self):
        """
        设置工作流步骤
        子类必须实现此方法来定义工作流的具体步骤
        """
        pass

    def add_step(
        self,
        name: str,
        description: str,
        execute_func: Callable[[WorkflowContext], Awaitable[Dict[str, Any]]],
        required_inputs: Optional[List[str]] = None,
        optional_inputs: Optional[List[str]] = None,
        outputs: Optional[List[str]] = None,
        max_retries: int = 3
    ):
        """
        添加工作流步骤

        Args:
            name: 步骤名称
            description: 步骤描述
            execute_func: 执行函数
            required_inputs: 必需的输入键
            optional_inputs: 可选的输入键
            outputs: 输出键
            max_retries: 最大重试次数
        """
        step = WorkflowStep(
            name=name,
            description=description,
            execute_func=execute_func,
            required_inputs=required_inputs or [],
            optional_inputs=optional_inputs or [],
            outputs=outputs or [],
            max_retries=max_retries
        )
        self.steps.append(step)

    async def execute(
        self,
        initial_context: Optional[Dict[str, Any]] = None,
        stop_on_error: bool = True
    ) -> WorkflowResult:
        """
        执行工作流

        Args:
            initial_context: 初始上下文数据
            stop_on_error: 遇到错误时是否停止

        Returns:
            WorkflowResult对象
        """
        # 初始化上下文
        if initial_context:
            self.context.update(initial_context)

        # 记录开始时间
        start_time = datetime.now()

        # 统计信息
        completed_steps = 0
        failed_steps = 0
        skipped_steps = 0
        step_results = []

        # 执行步骤
        for step in self.steps:
            # 验证输入
            if not step.validate_inputs(self.context):
                step.status = StepStatus.SKIPPED
                skipped_steps += 1
                step_results.append({
                    'name': step.name,
                    'status': 'skipped',
                    'reason': 'Missing required inputs'
                })
                continue

            # 执行步骤（带重试）
            step_success = await self._execute_step(step)

            # 记录结果
            step_results.append({
                'name': step.name,
                'status': step.status.value,
                'duration': step.duration,
                'result': step.result,
                'error': step.error
            })

            if step_success:
                completed_steps += 1
            else:
                failed_steps += 1
                if stop_on_error:
                    break

        # 记录结束时间
        end_time = datetime.now()

        # 构建结果
        success = failed_steps == 0 and completed_steps > 0

        result = WorkflowResult(
            success=success,
            workflow_name=self.name,
            total_steps=len(self.steps),
            completed_steps=completed_steps,
            failed_steps=failed_steps,
            skipped_steps=skipped_steps,
            context=self.context,
            step_results=step_results,
            error=None if success else f"{failed_steps} step(s) failed",
            start_time=start_time,
            end_time=end_time
        )

        return result

    async def _execute_step(self, step: WorkflowStep) -> bool:
        """
        执行单个步骤（带重试逻辑）

        Args:
            step: 工作流步骤

        Returns:
            是否执行成功
        """
        step.retry_count = 0

        while step.retry_count <= step.max_retries:
            try:
                step.status = StepStatus.RUNNING
                step.start_time = datetime.now()

                # 执行步骤函数
                result = await step.execute_func(self.context)

                # 更新上下文
                if result:
                    self.context.update(result)

                step.result = result
                step.status = StepStatus.COMPLETED
                step.end_time = datetime.now()

                return True

            except Exception as e:
                step.retry_count += 1
                step.error = str(e)

                if step.retry_count > step.max_retries:
                    step.status = StepStatus.FAILED
                    step.end_time = datetime.now()
                    return False

                # 等待后重试
                await asyncio.sleep(1 * step.retry_count)

        return False

    def get_step(self, step_name: str) -> Optional[WorkflowStep]:
        """获取指定名称的步骤"""
        for step in self.steps:
            if step.name == step_name:
                return step
        return None

    def get_status_summary(self) -> Dict[str, int]:
        """获取状态摘要"""
        summary = {status.value: 0 for status in StepStatus}
        for step in self.steps:
            summary[step.status.value] += 1
        return summary

    async def execute_from_step(
        self,
        step_name: str,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> WorkflowResult:
        """
        从指定步骤开始执行工作流

        Args:
            step_name: 起始步骤名称
            initial_context: 初始上下文

        Returns:
            WorkflowResult对象
        """
        # 找到起始步骤的索引
        start_index = None
        for i, step in enumerate(self.steps):
            if step.name == step_name:
                start_index = i
                break

        if start_index is None:
            raise ValueError(f"Step '{step_name}' not found in workflow")

        # 创建临时工作流，只包含从起始步骤开始的步骤
        original_steps = self.steps
        self.steps = self.steps[start_index:]

        try:
            result = await self.execute(initial_context)
            return result
        finally:
            # 恢复原始步骤列表
            self.steps = original_steps

    def reset(self):
        """重置工作流状态"""
        self.context = WorkflowContext()
        for step in self.steps:
            step.status = StepStatus.PENDING
            step.result = None
            step.error = None
            step.start_time = None
            step.end_time = None
            step.retry_count = 0

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} '{self.name}' ({len(self.steps)} steps)>"
