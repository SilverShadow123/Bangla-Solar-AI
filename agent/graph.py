
from typing import TypedDict, Annotated

from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from agent.llm import llm
from agent.prompts import SOLAR_AGENT_PROMPT
from tools.solar_tools import solar_tools


class SolarAgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def chatbot_node(state: SolarAgentState) -> dict:
    """Let the LLM respond or request a tool call."""

    messages = [
        SystemMessage(content=SOLAR_AGENT_PROMPT),
        *state["messages"],
    ]

    response = llm_with_tools.invoke(messages)

    return {"messages": [response]}


llm_with_tools = llm.bind_tools(solar_tools)


def build_solar_graph():
    graph = StateGraph(SolarAgentState)

    graph.add_node("chatbot", chatbot_node)
    graph.add_node("tools", ToolNode(solar_tools))

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
