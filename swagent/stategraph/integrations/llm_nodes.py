"""
LLM node integrations for StateGraph.
Provides utilities to wrap LLM calls as graph nodes.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable, List, Union
import asyncio

from swagent.stategraph.node import Node, NodeConfig


@dataclass
class LLMNodeConfig:
    """
    Configuration for LLM nodes.

    Attributes:
        name: Node name
        model: Model name/identifier
        temperature: Sampling temperature
        max_tokens: Maximum tokens in response
        system_prompt: Optional system prompt
        input_key: State key containing user input
        output_key: State key for LLM output
        messages_key: State key for chat messages (optional)
        prompt_template: Template for formatting input
        retry_count: Number of retries on failure
        timeout: Request timeout in seconds
    """
    name: str
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4096
    system_prompt: Optional[str] = None
    input_key: str = "input"
    output_key: str = "output"
    messages_key: Optional[str] = None
    prompt_template: Optional[str] = None
    retry_count: int = 2
    timeout: float = 60.0
    metadata: Dict[str, Any] = field(default_factory=dict)


def llm_node(
    llm_client: Any,
    config: Optional[LLMNodeConfig] = None,
    name: Optional[str] = None,
    **kwargs
) -> Node:
    """
    Create a graph node that wraps an LLM call.

    Args:
        llm_client: LLM client instance (must have async chat method)
        config: LLM node configuration
        name: Node name (overrides config.name)
        **kwargs: Additional config options

    Returns:
        Node instance

    Example:
        from swagent.llm import OpenAIClient

        llm = OpenAIClient.from_config_file()

        chat_node = llm_node(
            llm,
            name="chat",
            input_key="user_message",
            output_key="assistant_response"
        )

        graph.add_node("chat", chat_node)
    """
    # Build config
    if config is None:
        config = LLMNodeConfig(
            name=name or "llm_node",
            **kwargs
        )
    elif name:
        config.name = name

    async def llm_func(state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute LLM call."""
        # Build messages
        messages = []

        # Add system prompt
        if config.system_prompt:
            messages.append({
                "role": "system",
                "content": config.system_prompt
            })

        # Add history if messages_key specified
        if config.messages_key and config.messages_key in state:
            history = state[config.messages_key]
            if isinstance(history, list):
                messages.extend(history)

        # Get user input
        user_input = state.get(config.input_key, "")

        # Apply template if provided
        if config.prompt_template:
            user_content = config.prompt_template.format(
                input=user_input,
                **state
            )
        else:
            user_content = str(user_input)

        # Add user message
        messages.append({
            "role": "user",
            "content": user_content
        })

        # Call LLM
        response = await llm_client.chat(
            messages=messages,
            temperature=config.temperature,
            max_tokens=config.max_tokens
        )

        # Extract content
        output = response.content if hasattr(response, 'content') else str(response)

        result = {config.output_key: output}

        # Update messages history if tracking
        if config.messages_key:
            updated_messages = state.get(config.messages_key, [])[:]
            updated_messages.append({"role": "user", "content": user_content})
            updated_messages.append({"role": "assistant", "content": output})
            result[config.messages_key] = updated_messages

        return result

    # Create node with config
    node_config = NodeConfig(
        name=config.name,
        retry_count=config.retry_count,
        timeout=config.timeout,
        metadata=config.metadata
    )

    return Node(llm_func, config=node_config)


def create_chat_chain(
    llm_client: Any,
    system_prompt: str,
    name: str = "chat"
) -> Node:
    """
    Create a simple chat node with system prompt.

    Args:
        llm_client: LLM client
        system_prompt: System prompt for the chat
        name: Node name

    Returns:
        Configured chat node
    """
    config = LLMNodeConfig(
        name=name,
        system_prompt=system_prompt,
        input_key="user_input",
        output_key="response",
        messages_key="chat_history"
    )
    return llm_node(llm_client, config)
