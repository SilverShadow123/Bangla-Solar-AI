
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


LANGUAGE_HINT = {
    "bn": (
        "UI LANGUAGE: Bangla. Reply in Bangla (Bengali script) unless "
        "the user writes in English. Write numbers with Bengali digits "
        "when replying in Bangla."
    ),
    "en": "",
}


def build_assessment_context(assessment, inputs, language="en"):
    """Render the app's current assessment as text for the agent.

    This is what lets the chat answer questions about "my system" using
    exactly the numbers shown in the app, instead of recalculating.
    `language` is the app's UI language ("en" or "bn").
    """

    hint = LANGUAGE_HINT.get(language, "")

    if not assessment:
        return hint

    inputs = inputs or {}
    generation = assessment["generation"]
    electricity = assessment["electricity"]
    cost = assessment["cost"]
    savings = assessment.get("savings") or {}
    sizing = assessment.get("sizing") or {}
    battery = assessment.get("battery")

    payback = savings.get("payback_years")

    lines = [
        "CURRENT USER ASSESSMENT (computed by the app; authoritative):",
        f"- Location: {assessment['location']}",
        f"- Monthly bill: {inputs.get('monthly_bill_bdt', electricity['monthly_bill_bdt'])} BDT",
        f"- Roof area: {assessment['roof_area_sqm']} m2 "
        f"(usable {assessment['usable_roof_area_sqm']} m2)",
        f"- Estimated monthly consumption: "
        f"{electricity['monthly_consumption_kwh']} kWh",
        f"- Recommended capacity: {assessment['solar_capacity_kw']} kW "
        f"(limited by {sizing.get('limiting_factor', 'unknown')}; "
        f"roof limit {sizing.get('roof_limit_kw')} kW, "
        f"consumption-based {sizing.get('demand_based_kw')} kW)",
        f"- PVGIS yield: {generation.get('yearly_yield_kwh_per_kw')} "
        f"kWh per kW per year",
        f"- Estimated generation: {generation['monthly_generation_kwh']} "
        f"kWh/month, {generation['yearly_generation_kwh']} kWh/year",
        f"- Estimated cost: {cost['total_cost_bdt']} BDT "
        f"(solar {cost['solar_cost_bdt']}, battery {cost['battery_cost_bdt']})",
    ]

    assumptions = assessment.get("assumptions") or {}
    values = assumptions.get("values") or {}

    if values:
        lines.append(
            "- Assumptions used: "
            f"solar {values.get('costs.solar_cost_per_kw_bdt')} BDT/kW, "
            f"battery {values.get('costs.battery_cost_per_kwh_bdt')} BDT/kWh, "
            f"VAT {values.get('tariff.vat_rate')}, "
            f"sanctioned load {values.get('tariff.sanctioned_load_kw')} kW "
            f"x {values.get('tariff.demand_charge_per_kw_bdt')} BDT/kW demand charge, "
            f"roof {values.get('roof.area_per_kw_sqm')} m2/kW, "
            f"tariff: {assumptions.get('tariff_basis')}"
        )

    overrides = assumptions.get("overrides") or {}

    lines.append(
        f"- User overrides in effect: {overrides}" if overrides
        else "- User overrides in effect: none (stored defaults used)"
    )

    net = assessment.get("net_metering_info") or {}

    if net:
        lines.append(
            f"- Net metering: {'on' if net.get('enabled') else 'off'}; "
            f"surplus rate {net.get('surplus_rate_bdt_per_kwh')} BDT/kWh"
            f"{' (battery incentive applies)' if net.get('incentive_eligible') else ''}; "
            f"system within sanctioned load: {net.get('within_sanctioned_load')}"
        )

    for warning in assumptions.get("warnings") or []:
        lines.append(f"- Data warning: {warning}")

    if battery:
        lines.append(
            f"- Battery: {battery['battery_capacity_kwh']} kWh for "
            f"{battery['load_kw']} kW over {battery['backup_hours']} hours"
        )

    if savings:
        lines.append(
            f"- Average monthly bill: {savings['monthly_bill_before_bdt']} "
            f"BDT before solar, {savings['monthly_bill_after_bdt']} BDT "
            f"after (net of surplus payments); savings "
            f"{savings['monthly_savings_bdt']} BDT/month, "
            f"{savings['annual_savings_bdt']} BDT/year"
        )
        lines.append(
            "- Simple payback: "
            + (f"{payback} years" if payback is not None else "not available")
        )

    lines.extend([
        "",
        "Rules for this assessment:",
        "- When the user asks about their system, generation, cost, "
        "savings or payback, answer from these numbers.",
        "- Do not recompute them with different assumptions. For a "
        "what-if (different bill, roof, location or battery), call "
        "assess_solar_tool with the new values and say it is a "
        "what-if compared with the current assessment.",
        "- Pass the same assumption_overrides as listed above unless "
        "the user changes them.",
        "- If there are data warnings, mention that prices or "
        "tariffs are unverified when giving cost or payback figures.",
    ])

    if hint:
        lines.extend(["", hint])

    return "\n".join(lines)


def run_solar_agent(messages, assessment_context=""):
    """
    Run the LangGraph agent with the supplied conversation history and
    the text of the user's current assessment (see build_assessment_context).

    Returns the new messages, final answer, tool calls, tool results,
    and graph-node events.
    """

    new_messages = []
    tool_calls = []
    tool_results = []
    node_events = []
    answer = ""

    for event in solar_graph.stream(
        {
            "messages": messages,
            "assessment_context": assessment_context or "",
        },
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
