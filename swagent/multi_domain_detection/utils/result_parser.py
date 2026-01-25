"""
鲁棒的结果解析器 - 支持多种格式解析策略
"""
import json
import re
from typing import Dict, List, Any, Optional

from swagent.utils.logger import get_logger

logger = get_logger(__name__)


class RobustResultParser:
    """鲁棒的结果解析器"""

    def parse(self, raw_response: str, expected_tasks: List[str]) -> Dict[str, Any]:
        """
        多策略解析模型返回结果

        Args:
            raw_response: 模型原始返回
            expected_tasks: 期望的任务列表

        Returns:
            解析后的结果字典
        """
        # 策略1：标准JSON解析
        result = self._try_standard_json(raw_response, expected_tasks)
        if result:
            logger.debug("使用策略1：标准JSON解析成功")
            return result

        # 策略2：提取JSON代码块
        result = self._try_extract_json_block(raw_response, expected_tasks)
        if result:
            logger.debug("使用策略2：JSON代码块提取成功")
            return result

        # 策略3：处理<think>标签
        result = self._try_remove_think_tags(raw_response, expected_tasks)
        if result:
            logger.debug("使用策略3：移除think标签后解析成功")
            return result

        # 策略4：关键词提取 + 结构化重建
        result = self._try_extract_from_text(raw_response, expected_tasks)
        if result:
            logger.warning("使用策略4：从文本提取（置信度较低）")
            return result

        # 策略5：降级处理
        logger.error(f"所有解析策略失败，返回降级结果")
        return self._fallback_result(expected_tasks)

    def _try_standard_json(self, text: str, tasks: List[str]) -> Optional[Dict]:
        """策略1：标准JSON解析"""
        try:
            result = json.loads(text)
            if self._validate_result(result, tasks):
                return result
        except:
            pass
        return None

    def _try_extract_json_block(self, text: str, tasks: List[str]) -> Optional[Dict]:
        """策略2：提取```json```代码块"""
        try:
            # 匹配 ```json ... ```
            json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
                if self._validate_result(result, tasks):
                    return result

            # 匹配 ``` ... ```（无json标记）
            json_match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
                if self._validate_result(result, tasks):
                    return result
        except:
            pass
        return None

    def _try_remove_think_tags(self, text: str, tasks: List[str]) -> Optional[Dict]:
        """策略3：移除<think>标签后解析"""
        try:
            # 移除 <think>...</think>
            think_match = re.search(r'</think>\s*(.*)', text, re.DOTALL)
            if think_match:
                cleaned_text = think_match.group(1).strip()
                return self._try_standard_json(cleaned_text, tasks) or \
                       self._try_extract_json_block(cleaned_text, tasks)
        except:
            pass
        return None

    def _try_extract_from_text(self, text: str, tasks: List[str]) -> Optional[Dict]:
        """策略4：从自然语言文本中提取结构化信息"""
        result = {}

        for task in tasks:
            task_result = {
                "has_target": False,
                "description": "",
                "boundingbox": [],
                "count": 0,
                "confidence": 0.5  # 降低置信度
            }

            # 检测是否提到目标
            has_target_keywords = ["检测到", "发现", "存在", "识别到", "有"]
            no_target_keywords = ["未检测到", "未发现", "不存在", "没有"]

            text_lower = text.lower()

            if any(kw in text for kw in has_target_keywords):
                task_result["has_target"] = True

                # 提取数量
                count_match = re.search(r'(\d+)\s*[个处张台]', text)
                if count_match:
                    task_result["count"] = int(count_match.group(1))

                # 提取boundingbox（如果有）
                bbox_pattern = r'\[\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+\s*\]'
                bboxes = re.findall(bbox_pattern, text)
                if bboxes:
                    try:
                        task_result["boundingbox"] = [json.loads(bbox) for bbox in bboxes]
                    except:
                        pass

            elif any(kw in text for kw in no_target_keywords):
                task_result["has_target"] = False

            # 提取描述（取前200字符）
            task_result["description"] = text[:200] if text else "无法解析模型返回"

            result[task] = task_result

        return result if result else None

    def _validate_result(self, result: Dict, tasks: List[str]) -> bool:
        """验证结果是否有效"""
        if not isinstance(result, dict):
            return False

        # 如果是单任务结果（直接返回字典）
        if "has_target" in result:
            return True

        # 如果是多任务结果（包含任务名称的字典）
        for task in tasks:
            if task in result:
                return True

        return False

    def _fallback_result(self, tasks: List[str]) -> Dict[str, Any]:
        """降级结果（标记为需要人工审核）"""
        return {
            task: {
                "has_target": False,
                "error": True,
                "error_message": "模型返回格式无法解析",
                "needs_manual_review": True,
                "description": "解析失败，需要人工审核",
                "boundingbox": [],
                "count": 0
            }
            for task in tasks
        }

    def normalize_single_task_result(self, result: Dict, task_name: str) -> Dict[str, Dict]:
        """
        将单任务结果标准化为多任务格式

        Args:
            result: 单任务结果 {"has_target": true, ...}
            task_name: 任务名称

        Returns:
            多任务格式 {"task_name": {"has_target": true, ...}}
        """
        if task_name in result:
            # 已经是多任务格式
            return result
        else:
            # 转换为多任务格式
            return {task_name: result}
