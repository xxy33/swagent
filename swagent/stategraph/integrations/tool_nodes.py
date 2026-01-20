"""
Tool node integrations for StateGraph.
Provides utilities to wrap Tool instances as graph nodes.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, TYPE_CHECKING

from swagent.stategraph.node import Node, NodeConfig

if TYPE_CHECKING:
    from swagent.tools.base_tool import BaseTool


@dataclass
class ToolNodeConfig:
    """
    Configuration for Tool nodes.

    Attributes:
        name: Node name
        param_mapping: Mapping of state keys to tool parameters
        output_key: State key for tool output
        include_result_metadata: Include ToolResult metadata
        retry_count: Number of retries on failure
        timeout: Execution timeout in seconds
    """
    name: str
    param_mapping: Optional[Dict[str, str]] = None
    output_key: str = "tool_result"
    include_result_metadata: bool = False
    retry_count: int = 1
    timeout: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


def tool_node(
    tool: "BaseTool",
    config: Optional[ToolNodeConfig] = None,
    name: Optional[str] = None,
    **kwargs
) -> Node:
    """
    Create a graph node that wraps a Tool.

    Args:
        tool: Tool instance
        config: Tool node configuration
        name: Node name (overrides config.name, defaults to tool name)
        **kwargs: Additional config options

    Returns:
        Node instance

    Example:
        from swagent.tools import WebSearchTool

        search = WebSearchTool()

        search_node = tool_node(
            search,
            name="search",
            param_mapping={"query": "search_query"},
            output_key="search_results"
        )

        graph.add_node("search", search_node)
    """
    # Determine node name
    if name is None:
        name = tool.name if hasattr(tool, 'name') else 'tool_node'

    # Build config
    if config is None:
        config = ToolNodeConfig(name=name, **kwargs)
    elif name:
        config.name = name

    async def tool_func(state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool."""
        # Build parameters from state
        if config.param_mapping:
            params = {}
            for tool_param, state_key in config.param_mapping.items():
                if state_key in state:
                    params[tool_param] = state[state_key]
        else:
            # Get parameters from tool definition
            params = {}
            for param in tool.get_parameters():
                if param.name in state:
                    params[param.name] = state[param.name]
                elif param.default is not None:
                    params[param.name] = param.default

        # Execute tool
        result = await tool.safe_execute(**params)

        # Build output
        if result.success:
            output = {config.output_key: result.data}

            if config.include_result_metadata:
                output["tool_metadata"] = {
                    "tool_name": tool.name,
                    "success": True,
                    "metadata": result.metadata
                }
        else:
            output = {
                config.output_key: None,
                "tool_error": result.error
            }

            if config.include_result_metadata:
                output["tool_metadata"] = {
                    "tool_name": tool.name,
                    "success": False,
                    "error": result.error
                }

        return output

    # Create node with config
    node_config = NodeConfig(
        name=config.name,
        retry_count=config.retry_count,
        timeout=config.timeout,
        metadata=config.metadata
    )

    return Node(tool_func, config=node_config)


def create_tool_router(
    tools: List["BaseTool"],
    tool_selection_key: str = "selected_tool",
    output_key: str = "tool_result"
) -> Node:
    """
    Create a node that routes to different tools based on state.

    Args:
        tools: List of available tools
        tool_selection_key: State key containing selected tool name
        output_key: State key for tool output

    Returns:
        Node instance

    Example:
        router = create_tool_router(
            [search_tool, calculator_tool, file_tool],
            tool_selection_key="action",
            output_key="result"
        )

        graph.add_node("execute_tool", router)
    """
    # Build tool mapping
    tool_map = {tool.name: tool for tool in tools}

    async def router_func(state: Dict[str, Any]) -> Dict[str, Any]:
        """Route to appropriate tool."""
        selected = state.get(tool_selection_key)

        if not selected:
            return {
                output_key: None,
                "tool_error": "No tool selected"
            }

        if selected not in tool_map:
            return {
                output_key: None,
                "tool_error": f"Unknown tool: {selected}"
            }

        tool = tool_map[selected]

        # Get parameters
        params = {}
        for param in tool.get_parameters():
            if param.name in state:
                params[param.name] = state[param.name]

        # Execute
        result = await tool.safe_execute(**params)

        if result.success:
            return {output_key: result.data}
        else:
            return {
                output_key: None,
                "tool_error": result.error
            }

    return Node(
        router_func,
        config=NodeConfig(name="tool_router")
    )


def create_sequential_tools(
    tools: List["BaseTool"],
    input_output_chain: Optional[List[tuple]] = None
) -> List[Node]:
    """
    Create a sequence of tool nodes.

    Args:
        tools: List of tools to execute in sequence
        input_output_chain: List of (input_mapping, output_key) tuples

    Returns:
        List of Node instances

    Example:
        nodes = create_sequential_tools(
            [fetch_tool, parse_tool, store_tool],
            input_output_chain=[
                ({"url": "target_url"}, "raw_data"),
                ({"data": "raw_data"}, "parsed_data"),
                ({"content": "parsed_data"}, "storage_result")
            ]
        )
    """
    nodes = []

    for i, tool in enumerate(tools):
        if input_output_chain and i < len(input_output_chain):
            mapping, output = input_output_chain[i]
            config = ToolNodeConfig(
                name=f"{tool.name}_{i}",
                param_mapping=mapping,
                output_key=output
            )
        else:
            config = ToolNodeConfig(
                name=f"{tool.name}_{i}",
                output_key=f"result_{i}"
            )

        nodes.append(tool_node(tool, config))

    return nodes
