
from agent.llm import llm


def test_openrouter_connection():
    response = llm.invoke(
        "Reply with exactly: OpenRouter connection successful"
    )

    assert response.content
    print(response.content)
