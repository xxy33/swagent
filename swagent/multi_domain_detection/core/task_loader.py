"""
任务配置加载器
"""
import yaml
from pathlib import Path
from typing import Dict, List, Any

from swagent.utils.logger import get_logger

logger = get_logger(__name__)


class TaskLoader:
    """任务配置加载器"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            # 默认配置路径
            config_path = Path(__file__).parent.parent / "config" / "task_prompts.yaml"

        self.config_path = Path(config_path)
        self.tasks = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载任务配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"任务配置加载成功: {len(config)} 个任务")
            return config
        except Exception as e:
            logger.error(f"加载任务配置失败: {e}")
            raise

    def get_task(self, task_name: str) -> Dict[str, Any]:
        """获取单个任务配置"""
        if task_name not in self.tasks:
            raise ValueError(f"未知任务: {task_name}")
        return self.tasks[task_name]

    def get_tasks(self, task_names: List[str]) -> Dict[str, Any]:
        """获取多个任务配置"""
        return {name: self.get_task(name) for name in task_names}

    def get_all_task_names(self) -> List[str]:
        """获取所有任务名称"""
        return list(self.tasks.keys())

    def is_simple_task(self, task_name: str) -> bool:
        """判断是否为简单任务（可以合并调用）"""
        task = self.get_task(task_name)
        return task.get("complexity", "complex") == "simple"

    def get_simple_tasks(self, task_names: List[str]) -> List[str]:
        """获取简单任务列表"""
        return [name for name in task_names if self.is_simple_task(name)]

    def get_complex_tasks(self, task_names: List[str]) -> List[str]:
        """获取复杂任务列表"""
        return [name for name in task_names if not self.is_simple_task(name)]
