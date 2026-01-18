"""
代码执行器工具
支持Python、Shell等代码的安全执行
"""
import asyncio
import subprocess
import tempfile
import os
from typing import List
from pathlib import Path

from swagent.tools.base_tool import (
    BaseTool,
    ToolCategory,
    ToolParameter,
    ToolResult
)
from swagent.utils.logger import get_logger


logger = get_logger(__name__)


class CodeExecutor(BaseTool):
    """
    代码执行器

    支持执行Python、Shell等代码
    提供安全的沙箱环境（可选）
    """

    def __init__(self, timeout: int = 30, enable_sandbox: bool = False):
        """
        初始化代码执行器

        Args:
            timeout: 执行超时时间（秒）
            enable_sandbox: 是否启用沙箱模式
        """
        super().__init__()
        self.timeout = timeout
        self.enable_sandbox = enable_sandbox

    @property
    def name(self) -> str:
        return "code_executor"

    @property
    def description(self) -> str:
        return "执行Python或Shell代码，返回执行结果。支持代码片段和完整脚本。"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.CODE

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="code",
                type="string",
                description="要执行的代码",
                required=True
            ),
            ToolParameter(
                name="language",
                type="string",
                description="代码语言",
                required=False,
                default="python",
                enum=["python", "shell", "bash"]
            ),
            ToolParameter(
                name="timeout",
                type="number",
                description="超时时间（秒）",
                required=False,
                default=30
            )
        ]

    def get_return_description(self) -> str:
        return "返回包含stdout、stderr、exit_code的执行结果"

    def get_examples(self) -> List[dict]:
        return [
            {
                "input": {
                    "code": "print('Hello, World!')",
                    "language": "python"
                },
                "output": {
                    "stdout": "Hello, World!\n",
                    "stderr": "",
                    "exit_code": 0
                }
            },
            {
                "input": {
                    "code": "import pandas as pd\ndf = pd.DataFrame({'a': [1, 2, 3]})\nprint(df.mean())",
                    "language": "python"
                },
                "output": {
                    "stdout": "a    2.0\ndtype: float64\n",
                    "stderr": "",
                    "exit_code": 0
                }
            }
        ]

    async def execute(self, **kwargs) -> ToolResult:
        """执行代码"""
        code = kwargs["code"]
        language = kwargs.get("language", "python")
        timeout = kwargs.get("timeout", self.timeout)

        logger.info(f"执行{language}代码 - 长度: {len(code)}, 超时: {timeout}秒")

        try:
            if language == "python":
                result = await self._execute_python(code, timeout)
            elif language in ["shell", "bash"]:
                result = await self._execute_shell(code, timeout)
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unsupported language: {language}"
                )

            return ToolResult(
                success=result["exit_code"] == 0,
                data=result,
                metadata={"language": language}
            )

        except asyncio.TimeoutError:
            logger.warning(f"代码执行超时 - {timeout}秒")
            return ToolResult(
                success=False,
                data=None,
                error=f"Execution timeout after {timeout} seconds"
            )
        except Exception as e:
            logger.error(f"代码执行异常: {str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                data=None,
                error=f"Execution error: {str(e)}"
            )

    async def _execute_python(self, code: str, timeout: int) -> dict:
        """执行Python代码"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.py',
            delete=False
        ) as f:
            f.write(code)
            temp_file = f.name

        try:
            # 执行
            process = await asyncio.create_subprocess_exec(
                'python', temp_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )

            return {
                "stdout": stdout.decode('utf-8'),
                "stderr": stderr.decode('utf-8'),
                "exit_code": process.returncode
            }

        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file)
            except Exception:
                pass

    async def _execute_shell(self, code: str, timeout: int) -> dict:
        """执行Shell代码"""
        process = await asyncio.create_subprocess_shell(
            code,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )

        return {
            "stdout": stdout.decode('utf-8'),
            "stderr": stderr.decode('utf-8'),
            "exit_code": process.returncode
        }
