"""
Prompt构建器 - 支持单任务和多任务prompt生成
"""
from typing import List, Dict, Any

from swagent.utils.logger import get_logger
from .task_loader import TaskLoader

logger = get_logger(__name__)


class PromptBuilder:
    """Prompt构建器"""

    def __init__(self, task_loader: TaskLoader):
        self.task_loader = task_loader

    def build_single_task_prompt(self, task_name: str) -> str:
        """
        构建单任务prompt（带Few-shot示例）

        Args:
            task_name: 任务名称

        Returns:
            完整的prompt字符串
        """
        task_config = self.task_loader.get_task(task_name)

        prompt = f"""你是一个专业的遥感图像分析AI。

任务：{task_config['name']}
描述：{task_config['description']}

{task_config['prompt']}

重要提示：
1. 请严格按照上述JSON格式返回结果
2. boundingbox坐标必须是归一化坐标（0-1范围）
3. 格式为 [ymin, xmin, ymax, xmax]
4. 如果未检测到目标，has_target设为false
"""

        return prompt

    def build_multi_task_prompt(self, task_names: List[str]) -> str:
        """
        构建多任务prompt（简单任务合并）

        Args:
            task_names: 任务名称列表

        Returns:
            完整的prompt字符串
        """
        tasks_config = self.task_loader.get_tasks(task_names)

        prompt = "你是一个专业的遥感图像分析AI。请同时完成以下多个检测任务：\n\n"

        # 添加每个任务的说明
        for i, (task_name, config) in enumerate(tasks_config.items(), 1):
            prompt += f"""
## 任务{i}：{config['name']}
{config['description']}

{config['prompt']}

---

"""

        # 添加输出格式说明
        prompt += """
## 输出格式

请将所有任务的结果组合在一个JSON对象中返回，格式如下：

```json
{
"""

        for task_name in task_names:
            prompt += f'  "{task_name}": {{"has_target": true/false, ...}},\n'

        prompt += """}
```

重要提示：
1. 必须返回所有任务的结果
2. 每个任务的结果必须包含has_target字段
3. boundingbox坐标必须是归一化坐标（0-1范围）
4. 格式为 [ymin, xmin, ymax, xmax]
"""

        return prompt

    def build_prompt_for_tasks(
        self,
        simple_tasks: List[str],
        complex_tasks: List[str]
    ) -> Dict[str, str]:
        """
        为简单任务和复杂任务分别构建prompt

        Args:
            simple_tasks: 简单任务列表（合并调用）
            complex_tasks: 复杂任务列表（单独调用）

        Returns:
            prompt字典 {"multi": "...", "task1": "...", "task2": "..."}
        """
        prompts = {}

        # 简单任务合并
        if simple_tasks:
            if len(simple_tasks) == 1:
                # 只有一个简单任务，也单独调用
                prompts[simple_tasks[0]] = self.build_single_task_prompt(simple_tasks[0])
            else:
                # 多个简单任务，合并调用
                prompts["multi_simple"] = self.build_multi_task_prompt(simple_tasks)
                prompts["multi_simple_tasks"] = simple_tasks  # 记录包含的任务

        # 复杂任务单独调用
        for task in complex_tasks:
            prompts[task] = self.build_single_task_prompt(task)

        return prompts
