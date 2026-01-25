"""Progress tracker service with SSE support."""
import asyncio
from typing import Dict, Optional, Callable, AsyncGenerator
from datetime import datetime
from dataclasses import dataclass, field
import uuid
import json

from web.models.schemas import TaskStatus, ProgressEvent


@dataclass
class TaskInfo:
    """Information about a running task."""
    task_id: str
    session_id: str
    status: TaskStatus = TaskStatus.PENDING
    current: int = 0
    total: int = 0
    current_file: Optional[str] = None
    message: str = ""
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    subscribers: list = field(default_factory=list)


class ProgressTracker:
    """Tracks progress of detection tasks and provides SSE streams."""

    def __init__(self):
        self._tasks: Dict[str, TaskInfo] = {}
        self._lock = asyncio.Lock()

    async def create_task(self, session_id: str, total: int) -> str:
        """Create a new task and return its ID."""
        task_id = str(uuid.uuid4())
        async with self._lock:
            self._tasks[task_id] = TaskInfo(
                task_id=task_id,
                session_id=session_id,
                total=total,
                status=TaskStatus.PENDING,
                message="任务已创建"
            )
        return task_id

    async def start_task(self, task_id: str) -> None:
        """Mark task as started."""
        async with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].status = TaskStatus.RUNNING
                self._tasks[task_id].started_at = datetime.now()
                self._tasks[task_id].message = "任务开始执行"
        await self._notify_subscribers(task_id)

    async def update_progress(
        self,
        task_id: str,
        current: int,
        current_file: Optional[str] = None,
        message: Optional[str] = None
    ) -> None:
        """Update task progress."""
        async with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                task.current = current
                if current_file:
                    task.current_file = current_file
                if message:
                    task.message = message
                else:
                    task.message = f"处理中: {current}/{task.total}"
        await self._notify_subscribers(task_id)

    async def complete_task(self, task_id: str, message: str = "任务完成") -> None:
        """Mark task as completed."""
        async with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                task.message = message
                task.current = task.total
        await self._notify_subscribers(task_id)

    async def fail_task(self, task_id: str, error: str) -> None:
        """Mark task as failed."""
        async with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now()
                task.error = error
                task.message = f"任务失败: {error}"
        await self._notify_subscribers(task_id)

    async def stop_task(self, task_id: str) -> bool:
        """Stop a running task."""
        async with self._lock:
            if task_id in self._tasks:
                task = self._tasks[task_id]
                if task.status == TaskStatus.RUNNING:
                    task.status = TaskStatus.STOPPED
                    task.completed_at = datetime.now()
                    task.message = "任务已停止"
                    return True
        await self._notify_subscribers(task_id)
        return False

    async def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """Get task information."""
        async with self._lock:
            return self._tasks.get(task_id)

    async def get_progress_event(self, task_id: str) -> Optional[ProgressEvent]:
        """Get current progress as an event."""
        task = await self.get_task(task_id)
        if not task:
            return None

        percentage = (task.current / task.total * 100) if task.total > 0 else 0
        return ProgressEvent(
            task_id=task_id,
            current=task.current,
            total=task.total,
            percentage=round(percentage, 1),
            current_file=task.current_file,
            message=task.message,
            status=task.status
        )

    async def _notify_subscribers(self, task_id: str) -> None:
        """Notify all subscribers of a task update."""
        # Get subscribers and task info without holding lock during notification
        async with self._lock:
            if task_id not in self._tasks:
                return
            task = self._tasks[task_id]
            subscribers = list(task.subscribers)
            # Build event data while holding lock
            percentage = (task.current / task.total * 100) if task.total > 0 else 0
            event = ProgressEvent(
                task_id=task_id,
                current=task.current,
                total=task.total,
                percentage=round(percentage, 1),
                current_file=task.current_file,
                message=task.message,
                status=task.status
            )

        # Notify subscribers without holding lock
        for queue in subscribers:
            try:
                await queue.put(event)
            except Exception:
                pass

    async def subscribe(self, task_id: str) -> AsyncGenerator[str, None]:
        """Subscribe to task progress updates via SSE."""
        queue: asyncio.Queue = asyncio.Queue()

        async with self._lock:
            if task_id not in self._tasks:
                yield f"data: {json.dumps({'error': 'Task not found'})}\n\n"
                return
            self._tasks[task_id].subscribers.append(queue)

        try:
            # Send initial state
            event = await self.get_progress_event(task_id)
            if event:
                yield f"data: {event.model_dump_json()}\n\n"

            # Stream updates
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {event.model_dump_json()}\n\n"

                    # Stop streaming if task is done
                    if event.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.STOPPED]:
                        break
                except asyncio.TimeoutError:
                    # Send keepalive
                    yield f": keepalive\n\n"
        finally:
            async with self._lock:
                if task_id in self._tasks:
                    try:
                        self._tasks[task_id].subscribers.remove(queue)
                    except ValueError:
                        pass


# Global progress tracker instance
progress_tracker = ProgressTracker()
