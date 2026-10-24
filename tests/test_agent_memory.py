
import sys
from pathlib import Path
from unittest.mock import patch

# Add the project root to Python's import path.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    ToolMessage,
)

from agent.graph import solar_graph


def test_agent_receives_previous_conversation():
    """Verify that conversation history is passed to the graph."""

    history = [
        HumanMessage(content="Estimate solar generation."),
        AIMessage(content="Daily generation is 12.6 kWh."),
    ]

    follow_up = HumanMessage(
        content="What is the monthly generation?"
    )

    messages = history + [follow_up]

    mocked_response = AIMessage(
        content="Monthly generation is 378 kWh."
    )

    with patch.object(solar_graph, "stream") as mock_stream:
        mock_stream.return_value = iter([
            {
                "agent": {
                    "messages": [mocked_response]
                }
            }
        ])

        events = list(
            solar_graph.stream(
                {"messages": messages},
                stream_mode="updates",
            )
        )

    assert len(events) == 1

    response_messages = events[0]["agent"]["messages"]
    assert response_messages[0].content == (
        "Monthly generation is 378 kWh."
    )

    # Verify that the graph received the complete conversation.
    args, kwargs = mock_stream.call_args
    received_messages = args[0]["messages"]

    assert len(received_messages) == 3
    assert isinstance(received_messages[0], HumanMessage)
    assert isinstance(received_messages[1], AIMessage)
    assert isinstance(received_messages[2], HumanMessage)
    assert received_messages[2].content == (
        "What is the monthly generation?"
    )


def test_tool_call_and_result_can_be_preserved():
    """Verify that tool-call and tool-result messages retain their IDs."""

    tool_call = AIMessage(
        content="",
        tool_calls=[
            {
                "name": "solar_generation_tool",
                "args": {"capacity_kw": 3.5},
                "id": "call_123",
                "type": "tool_call",
            }
        ],
    )

    tool_result = ToolMessage(
        content="Daily generation: 12.6 kWh",
        tool_call_id="call_123",
        name="solar_generation_tool",
    )

    history = [tool_call, tool_result]

    assert history[0].tool_calls[0]["name"] == (
        "solar_generation_tool"
    )
    assert history[0].tool_calls[0]["id"] == "call_123"
    assert isinstance(history[1], ToolMessage)
    assert history[1].tool_call_id == "call_123"
    assert history[1].content == "Daily generation: 12.6 kWh"
