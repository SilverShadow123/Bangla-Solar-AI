
import sys
from pathlib import Path

# Resolve and add the project root before importing agent.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

print(f"Project root: {PROJECT_ROOT}")
print(f"Agent folder exists: {(PROJECT_ROOT / 'agent').is_dir()}")

from langchain_core.messages import HumanMessage
from agent.graph import solar_graph


def main():
    history = []

    questions = [
        "Calculate daily solar generation for a 3.5 kW system using 4.5 peak sun hours and 80% efficiency.",
        "Change the efficiency to 90%, keeping everything else the same.",
        "Now calculate monthly generation over 30 days.",
    ]

    for question in questions:
        print("\n" + "=" * 70)
        print("QUESTION:", question)

        previous_count = len(history)

        result = solar_graph.invoke({
            "messages": history + [HumanMessage(content=question)]
        })

        history = result["messages"]
        new_messages = history[previous_count:]

        for message in new_messages:
            tool_calls = getattr(message, "tool_calls", [])

            if tool_calls:
                print("\nTOOL CALL:")
                for call in tool_calls:
                    print("Name:", call["name"])
                    print("Arguments:", call["args"])

            elif message.type == "tool":
                print("\nTOOL RESULT:")
                print(message.content)

            elif message.type == "ai" and message.content:
                print("\nFINAL ANSWER:")
                print(message.content)

    print("\nConversation memory test completed.")


if __name__ == "__main__":
    main()
