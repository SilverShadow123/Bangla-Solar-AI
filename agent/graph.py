from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from agent.llm import llm
from agent.prompts import SOLAR_AGENT_PROMPT
from tools.solar_tools import solar_tools


class SolarAgentState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]

    # The app's current assessment, rendered as text. It is rebuilt on
    # every turn, so it always reflects the latest Assess click.
    assessment_context: str


llm_with_tools = llm.bind_tools(solar_tools)


def chatbot_node(state: SolarAgentState) -> dict:
    """Let the LLM respond or request a tool call."""

    system_prompt = SOLAR_AGENT_PROMPT
    assessment_context = state.get("assessment_context")

    if assessment_context:
        system_prompt = f"{system_prompt}\n\n{assessment_context}"

    messages = [
        SystemMessage(content=system_prompt),
        *state["messages"],
    ]

    response = llm_with_tools.invoke(messages)

    return {"messages": [response]}


def build_solar_graph():
    graph = StateGraph(SolarAgentState)

    graph.add_node("chatbot", chatbot_node)
    graph.add_node("tools", ToolNode(solar_tools, handle_tool_errors=True))

    graph.add_edge(START, "chatbot")

    graph.add_conditional_edges(
        "chatbot",
        tools_condition,
        {
            "tools": "tools",
            END: END,
        },
    )

    graph.add_edge("tools", "chatbot")

    return graph.compile()


solar_graph = build_solar_graph()
