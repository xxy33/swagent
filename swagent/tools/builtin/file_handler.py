"""
文件处理器工具
支持文件的读写、检索等操作
"""
import os
import json
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


class FileHandler(BaseTool):
    """
    文件处理器

    支持文件的读取、写入、列表等操作
    """

    def __init__(self, base_path: str = "./data"):
        """
        初始化文件处理器

        Args:
            base_path: 基础路径（文件操作的根目录）
        """
        super().__init__()
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return "file_handler"

    @property
    def description(self) -> str:
        return "文件处理工具，支持读取、写入、列表、删除等文件操作"

    @property
    def category(self) -> ToolCategory:
        return ToolCategory.FILE

    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="operation",
                type="string",
                description="操作类型",
                required=True,
                enum=["read", "write", "list", "delete", "exists"]
            ),
            ToolParameter(
                name="file_path",
                type="string",
                description="文件路径（相对于base_path）",
                required=False
            ),
            ToolParameter(
                name="content",
                type="string",
                description="文件内容（用于write操作）",
                required=False
            ),
            ToolParameter(
                name="encoding",
                type="string",
                description="文件编码",
                required=False,
                default="utf-8"
            )
        ]

    def get_return_description(self) -> str:
        return "根据操作类型返回相应结果：read返回文件内容，write返回成功信息，list返回文件列表，delete返回删除结果，exists返回是否存在"

    def get_examples(self) -> List[dict]:
        return [
            {
                "input": {
                    "operation": "write",
                    "file_path": "test.txt",
                    "content": "Hello, World!"
                },
                "output": {
                    "message": "File written successfully",
                    "path": "data/test.txt"
                }
            },
            {
                "input": {
                    "operation": "read",
                    "file_path": "test.txt"
                },
                "output": {
                    "content": "Hello, World!",
                    "size": 13
                }
            }
        ]

    async def execute(self, **kwargs) -> ToolResult:
        """执行文件操作"""
        operation = kwargs["operation"]

        logger.info(f"文件操作 - {operation}")

        try:
            if operation == "read":
                return await self._read_file(**kwargs)
            elif operation == "write":
                return await self._write_file(**kwargs)
            elif operation == "list":
                return await self._list_files(**kwargs)
            elif operation == "delete":
                return await self._delete_file(**kwargs)
            elif operation == "exists":
                return await self._check_exists(**kwargs)
            else:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Unknown operation: {operation}"
                )

        except Exception as e:
            logger.error(f"文件操作异常: {str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                data=None,
                error=str(e)
            )

    async def _read_file(self, **kwargs) -> ToolResult:
        """读取文件"""
        file_path = kwargs.get("file_path")
        if not file_path:
            return ToolResult(
                success=False,
                data=None,
                error="file_path is required for read operation"
            )

        encoding = kwargs.get("encoding", "utf-8")
        full_path = self.base_path / file_path

        if not full_path.exists():
            return ToolResult(
                success=False,
                data=None,
                error=f"File not found: {file_path}"
            )

        content = full_path.read_text(encoding=encoding)

        return ToolResult(
            success=True,
            data={
                "content": content,
                "size": len(content),
                "path": str(full_path)
            }
        )

    async def _write_file(self, **kwargs) -> ToolResult:
        """写入文件"""
        file_path = kwargs.get("file_path")
        content = kwargs.get("content")

        if not file_path:
            return ToolResult(
                success=False,
                data=None,
                error="file_path is required for write operation"
            )

        if content is None:
            return ToolResult(
                success=False,
                data=None,
                error="content is required for write operation"
            )

        encoding = kwargs.get("encoding", "utf-8")
        full_path = self.base_path / file_path

        # 确保目录存在
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        full_path.write_text(content, encoding=encoding)

        return ToolResult(
            success=True,
            data={
                "message": "File written successfully",
                "path": str(full_path),
                "size": len(content)
            }
        )

    async def _list_files(self, **kwargs) -> ToolResult:
        """列出文件"""
        file_path = kwargs.get("file_path", "")
        full_path = self.base_path / file_path

        if not full_path.exists():
            return ToolResult(
                success=False,
                data=None,
                error=f"Path not found: {file_path}"
            )

        if full_path.is_file():
            return ToolResult(
                success=False,
                data=None,
                error=f"Path is a file, not a directory: {file_path}"
            )

        # 列出文件
        files = []
        for item in full_path.iterdir():
            files.append({
                "name": item.name,
                "type": "file" if item.is_file() else "directory",
                "size": item.stat().st_size if item.is_file() else None
            })

        return ToolResult(
            success=True,
            data={
                "files": files,
                "count": len(files),
                "path": str(full_path)
            }
        )

    async def _delete_file(self, **kwargs) -> ToolResult:
        """删除文件"""
        file_path = kwargs.get("file_path")
        if not file_path:
            return ToolResult(
                success=False,
                data=None,
                error="file_path is required for delete operation"
            )

        full_path = self.base_path / file_path

        if not full_path.exists():
            return ToolResult(
                success=False,
                data=None,
                error=f"File not found: {file_path}"
            )

        if full_path.is_file():
            full_path.unlink()
        else:
            return ToolResult(
                success=False,
                data=None,
                error=f"Path is a directory: {file_path}"
            )

        return ToolResult(
            success=True,
            data={
                "message": "File deleted successfully",
                "path": str(full_path)
            }
        )

    async def _check_exists(self, **kwargs) -> ToolResult:
        """检查文件是否存在"""
        file_path = kwargs.get("file_path")
        if not file_path:
            return ToolResult(
                success=False,
                data=None,
                error="file_path is required for exists operation"
            )

        full_path = self.base_path / file_path
        exists = full_path.exists()

        return ToolResult(
            success=True,
            data={
                "exists": exists,
                "path": str(full_path),
                "type": "file" if exists and full_path.is_file() else (
                    "directory" if exists and full_path.is_dir() else None
                )
            }
        )
