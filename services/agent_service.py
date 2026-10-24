
from langchain_core.messages import AIMessage, ToolMessage

from agent.graph import solar_graph


def format_message_content(content):
    """Convert model message content into displayable text."""

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []

        for item in content:
            if isinstance(item, dict):
                text = item.get("text")

                if text:
                    parts.append(str(text))

            elif isinstance(item, str):
                parts.append(item)

        return "\n".join(parts)

    return str(content)


def run_solar_agent(messages):
    """
    Run the LangGraph agent with the supplied conversation history.

    Returns the new messages, final answer, tool calls, tool results,
    and graph-node events.
    """

    new_messages = []
    tool_calls = []
    tool_results = []
    node_events = []
    answer = ""

    for event in solar_graph.stream(
        {"messages": messages},
        stream_mode="updates",
    ):
        for node_name, update in event.items():
            node_events.append(node_name)

            node_messages = update.get("messages", [])

            if not isinstance(node_messages, list):
                node_messages = [node_messages]

            for message in node_messages:
                new_messages.append(message)

                if isinstance(message, AIMessage) and message.tool_calls:
                    for call in message.tool_calls:
                        tool_calls.append(
                            {
                                "name": call["name"],
                                "args": call.get("args", {}),
                                "id": call.get("id"),
                            }
                        )

                elif isinstance(message, ToolMessage):
                    tool_results.append(
                        {
                            "name": message.name,
                            "tool_call_id": message.tool_call_id,
                            "result": format_message_content(
                                message.content
                            ),
                        }
                    )

                elif isinstance(message, AIMessage) and message.content:
                    answer = format_message_content(message.content)

    return {
        "messages": new_messages,
        "answer": answer,
        "tool_calls": tool_calls,
        "tool_results": tool_results,
        "node_events": node_events,
    }
