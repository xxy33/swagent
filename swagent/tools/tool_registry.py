"""
工具注册中心
管理所有可用工具的注册、查询和调用
"""
from typing import Dict, List, Optional, Type, Any
from swagent.tools.base_tool import BaseTool, ToolResult, ToolCategory
from swagent.utils.logger import get_logger


logger = get_logger(__name__)


class ToolRegistry:
    """
    工具注册中心

    职责:
    - 管理工具的注册和注销
    - 提供工具查询接口
    - 支持工具的统一调用
    - 生成工具列表供LLM使用
    """

    def __init__(self):
        """初始化工具注册中心"""
        self._tools: Dict[str, BaseTool] = {}
        self._tools_by_category: Dict[ToolCategory, List[str]] = {}
        logger.info("工具注册中心初始化完成")

    def register(self, tool: BaseTool) -> None:
        """
        注册工具

        Args:
            tool: 工具实例

        Raises:
            ValueError: 如果工具名称已存在
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")

        self._tools[tool.name] = tool

        # 按类别索引
        category = tool.category
        if category not in self._tools_by_category:
            self._tools_by_category[category] = []
        self._tools_by_category[category].append(tool.name)

        logger.info(f"工具注册成功 - {tool.name} ({category.value})")

    def register_class(self, tool_class: Type[BaseTool]) -> None:
        """
        注册工具类（自动实例化）

        Args:
            tool_class: 工具类
        """
        tool = tool_class()
        self.register(tool)

    def unregister(self, tool_name: str) -> bool:
        """
        注销工具

        Args:
            tool_name: 工具名称

        Returns:
            是否成功注销
        """
        if tool_name not in self._tools:
            return False

        tool = self._tools[tool_name]
        category = tool.category

        # 从类别索引中移除
        if category in self._tools_by_category:
            self._tools_by_category[category].remove(tool_name)

        del self._tools[tool_name]
        logger.info(f"工具注销成功 - {tool_name}")
        return True

    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """
        获取工具实例

        Args:
            tool_name: 工具名称

        Returns:
            工具实例，如果不存在则返回None
        """
        return self._tools.get(tool_name)

    def has_tool(self, tool_name: str) -> bool:
        """检查工具是否存在"""
        return tool_name in self._tools

    def list_tools(
        self,
        category: Optional[ToolCategory] = None
    ) -> List[str]:
        """
        列出所有工具名称

        Args:
            category: 按类别过滤（可选）

        Returns:
            工具名称列表
        """
        if category is None:
            return list(self._tools.keys())
        else:
            return self._tools_by_category.get(category, [])

    def get_tools_info(
        self,
        category: Optional[ToolCategory] = None
    ) -> List[Dict[str, Any]]:
        """
        获取工具信息列表

        Args:
            category: 按类别过滤（可选）

        Returns:
            工具信息列表
        """
        tool_names = self.list_tools(category)
        return [
            {
                "name": name,
                "description": self._tools[name].description,
                "category": self._tools[name].category.value
            }
            for name in tool_names
        ]

    def to_openai_functions(
        self,
        tool_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        转换为OpenAI Function Calling格式

        Args:
            tool_names: 要转换的工具名称列表，None表示全部

        Returns:
            OpenAI functions列表
        """
        if tool_names is None:
            tool_names = self.list_tools()

        functions = []
        for name in tool_names:
            tool = self.get_tool(name)
            if tool:
                functions.append(tool.to_openai_function())

        return functions

    def to_mcp_tools(
        self,
        tool_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        转换为MCP工具格式

        Args:
            tool_names: 要转换的工具名称列表，None表示全部

        Returns:
            MCP工具列表
        """
        if tool_names is None:
            tool_names = self.list_tools()

        tools = []
        for name in tool_names:
            tool = self.get_tool(name)
            if tool:
                tools.append(tool.to_mcp_tool())

        return tools

    async def execute_tool(
        self,
        tool_name: str,
        **kwargs
    ) -> ToolResult:
        """
        执行工具

        Args:
            tool_name: 工具名称
            **kwargs: 工具参数

        Returns:
            工具执行结果
        """
        tool = self.get_tool(tool_name)

        if tool is None:
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool '{tool_name}' not found"
            )

        logger.info(f"执行工具 - {tool_name}, 参数: {kwargs}")

        try:
            result = await tool.safe_execute(**kwargs)
            logger.info(f"工具执行完成 - {tool_name}, 成功: {result.success}")
            return result
        except Exception as e:
            logger.error(f"工具执行异常 - {tool_name}: {str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool execution error: {str(e)}"
            )

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取注册统计信息

        Returns:
            统计信息
        """
        category_counts = {
            category.value: len(tools)
            for category, tools in self._tools_by_category.items()
        }

        return {
            "total_tools": len(self._tools),
            "by_category": category_counts,
            "tool_names": list(self._tools.keys())
        }

    def clear(self) -> None:
        """清空所有注册的工具"""
        self._tools.clear()
        self._tools_by_category.clear()
        logger.info("工具注册中心已清空")

    def __len__(self) -> int:
        """返回注册的工具数量"""
        return len(self._tools)

    def __contains__(self, tool_name: str) -> bool:
        """支持 'tool_name' in registry 语法"""
        return tool_name in self._tools

    def __repr__(self) -> str:
        return f"<ToolRegistry(tools={len(self._tools)})>"


# 全局工具注册中心实例
_global_registry: Optional[ToolRegistry] = None


def get_global_registry() -> ToolRegistry:
    """
    获取全局工具注册中心

    Returns:
        全局ToolRegistry实例
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def register_tool(tool: BaseTool) -> None:
    """
    注册工具到全局注册中心

    Args:
        tool: 工具实例
    """
    registry = get_global_registry()
    registry.register(tool)


def register_tool_class(tool_class: Type[BaseTool]) -> None:
    """
    注册工具类到全局注册中心

    Args:
        tool_class: 工具类
    """
    registry = get_global_registry()
    registry.register_class(tool_class)
