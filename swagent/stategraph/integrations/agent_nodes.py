"""
Agent node integrations for StateGraph.
Provides utilities to wrap Agent instances as graph nodes.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, TYPE_CHECKING

from swagent.stategraph.node import Node, NodeConfig

if TYPE_CHECKING:
    from swagent.core.base_agent import BaseAgent
    from swagent.core.message import Message


@dataclass
class AgentNodeConfig:
    """
    Configuration for Agent nodes.

    Attributes:
        name: Node name
        input_key: State key containing input for agent
        output_key: State key for agent output
        context_key: Optional key for additional context
        message_format: Whether to use Message objects
        include_metadata: Include agent metadata in output
        retry_count: Number of retries on failure
        timeout: Execution timeout in seconds
    """
    name: str
    input_key: str = "input"
    output_key: str = "output"
    context_key: Optional[str] = None
    message_format: bool = False
    include_metadata: bool = False
    retry_count: int = 1
    timeout: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


def agent_node(
    agent: "BaseAgent",
    config: Optional[AgentNodeConfig] = None,
    name: Optional[str] = None,
    **kwargs
) -> Node:
    """
    Create a graph node that wraps an Agent.

    Args:
        agent: Agent instance
        config: Agent node configuration
        name: Node name (overrides config.name, defaults to agent name)
        **kwargs: Additional config options

    Returns:
        Node instance

    Example:
        from swagent.agents import ReactAgent

        analyst = ReactAgent(config=AnalystConfig)

        analyst_node = agent_node(
            analyst,
            name="analyze",
            input_key="data",
            output_key="analysis"
        )

        graph.add_node("analyze", analyst_node)
    """
    # Determine node name
    if name is None:
        name = getattr(agent.config, 'name', 'agent_node') if hasattr(agent, 'config') else 'agent_node'

    # Build config
    if config is None:
        config = AgentNodeConfig(name=name, **kwargs)
    elif name:
        config.name = name

    async def agent_func(state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent."""
        from swagent.core.message import Message, MessageType

        # Get input
        input_content = state.get(config.input_key, "")

        # Get additional context
        context = state.get(config.context_key, {}) if config.context_key else {}

        if config.message_format:
            # Create Message object
            message = Message(
                sender="stategraph",
                sender_name="StateGraph",
                receiver=agent.agent_id,
                receiver_name=agent.config.name,
                content=str(input_content),
                msg_type=MessageType.TASK,
                metadata=context
            )

            # Run agent
            response = await agent.run(message)
            output = response.content

            result = {config.output_key: output}

            if config.include_metadata:
                result["agent_metadata"] = {
                    "agent_id": agent.agent_id,
                    "agent_name": agent.config.name,
                    "message_type": response.msg_type.value
                }
        else:
            # Use simple chat interface
            if hasattr(agent, 'chat'):
                output = await agent.chat(str(input_content))
            else:
                # Fallback to run
                message = Message(
                    sender="stategraph",
                    sender_name="StateGraph",
                    receiver=agent.agent_id,
                    receiver_name=getattr(agent.config, 'name', 'Agent'),
                    content=str(input_content),
                    msg_type=MessageType.TASK
                )
                response = await agent.run(message)
                output = response.content

            result = {config.output_key: output}

        return result

    # Create node with config
    node_config = NodeConfig(
        name=config.name,
        retry_count=config.retry_count,
        timeout=config.timeout,
        metadata=config.metadata
    )

    return Node(agent_func, config=node_config)


def create_agent_pipeline(
    agents: list,
    input_key: str = "input",
    output_key: str = "output"
) -> list:
    """
    Create a pipeline of agent nodes.

    Args:
        agents: List of agents
        input_key: Initial input key
        output_key: Final output key

    Returns:
        List of Node instances

    Example:
        nodes = create_agent_pipeline(
            [research_agent, analysis_agent, summary_agent],
            input_key="topic",
            output_key="report"
        )

        for i, node in enumerate(nodes):
            graph.add_node(f"step_{i}", node)
    """
    nodes = []
    current_key = input_key

    for i, agent in enumerate(agents):
        is_last = i == len(agents) - 1
        next_key = output_key if is_last else f"intermediate_{i}"

        config = AgentNodeConfig(
            name=f"agent_{i}",
            input_key=current_key,
            output_key=next_key
        )

        nodes.append(agent_node(agent, config))
        current_key = next_key

    return nodes
