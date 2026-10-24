
from langchain_core.messages import HumanMessage

from agent.graph import solar_graph


def test_graph_answers_solar_question():
    result = solar_graph.invoke({
        "messages": [
            HumanMessage(
                content=(
                    "Estimate monthly solar generation for a "
                    "3.5 kW solar system in Bangladesh. "
                    "Use the solar generation tool."
                )
            )
        ]
    })

    assert result["messages"]
    assert result["messages"][-1].content
