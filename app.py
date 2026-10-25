
import streamlit as st
from langchain_core.messages import HumanMessage

from services.solar_engine import assess_solar_feasibility
from tools.config import AssumptionsError, resolve_assumptions
from services.report_service import (
    generate_solar_report,
    generate_solar_report_pdf,
)
from services.agent_service import (
    build_assessment_context,
    run_solar_agent,
)


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Bangla Solar AI",
    page_icon="☀️",
    layout="wide",
)

st.title("☀️ Bangla Solar AI")
st.caption("বাংলায় আপনার ছাদের সৌরবিদ্যুৎ সম্ভাব্যতা যাচাই করুন")


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

if "agent_messages" not in st.session_state:
    st.session_state["agent_messages"] = []

if "assessment" not in st.session_state:
    st.session_state["assessment"] = None

if "report" not in st.session_state:
    st.session_state["report"] = None

if "assessment_inputs" not in st.session_state:
    st.session_state["assessment_inputs"] = None

if "report_pdf" not in st.session_state:
    st.session_state["report_pdf"] = None


# --------------------------------------------------
# SIDEBAR: SOLAR ASSESSMENT
# --------------------------------------------------

with st.sidebar:
    st.header("Solar Assessment")

    location = st.text_input(
        "Location",
        placeholder="e.g. Barishal, Bangladesh",
    )

    monthly_bill = st.number_input(
        "Monthly electricity bill (BDT)",
        min_value=0.0,
        value=3000.0,
        step=100.0,
    )

    roof_area = st.number_input(
        "Roof area (m²)",
        min_value=1.0,
        value=50.0,
        step=5.0,
    )

    needs_battery = st.checkbox("I need battery backup")

    backup_load = 0.5
    backup_hours = 4.0

    if needs_battery:
        backup_load = st.number_input(
            "Backup load (kW)",
            min_value=0.1,
            value=0.5,
            step=0.1,
        )

        backup_hours = st.number_input(
            "Backup duration (hours)",
            min_value=1.0,
            value=4.0,
            step=1.0,
        )

    # Defaults come from data/assumptions.json. Only values the user
    # changes are sent as overrides.
    assumption_overrides = {}

    try:
        defaults = resolve_assumptions()
    except AssumptionsError as error:
        defaults = None
        st.error(f"Assumptions file problem: {error}")

    if defaults is not None:
        with st.expander("Advanced: use your own prices"):
            st.caption(
                "Defaults come from data/assumptions.json. Change a value "
                "to use your own installer quote or the figures on your bill."
            )

            solar_cost = st.number_input(
                "Solar cost per kW (BDT)",
                min_value=1.0,
                value=float(defaults["costs"]["solar_cost_per_kw_bdt"]),
                step=5000.0,
            )

            battery_cost = st.number_input(
                "Battery cost per kWh (BDT)",
                min_value=1.0,
                value=float(defaults["costs"]["battery_cost_per_kwh_bdt"]),
                step=1000.0,
            )

            vat_percent = st.number_input(
                "VAT on bill (%)",
                min_value=0.0,
                max_value=100.0,
                value=float(defaults["tariff"]["vat_rate"]) * 100,
                step=0.5,
            )

            demand_charge = st.number_input(
                "Demand charge on bill (BDT/month)",
                min_value=0.0,
                value=float(defaults["tariff"]["demand_charge_bdt"]),
                step=10.0,
            )

            area_per_kw = st.number_input(
                "Roof area per kW of panels (m²)",
                min_value=2.0,
                max_value=30.0,
                value=float(defaults["roof"]["area_per_kw_sqm"]),
                step=0.5,
            )

        if solar_cost != float(defaults["costs"]["solar_cost_per_kw_bdt"]):
            assumption_overrides["costs.solar_cost_per_kw_bdt"] = solar_cost

        if battery_cost != float(defaults["costs"]["battery_cost_per_kwh_bdt"]):
            assumption_overrides["costs.battery_cost_per_kwh_bdt"] = battery_cost

        if abs(vat_percent / 100 - float(defaults["tariff"]["vat_rate"])) > 1e-9:
            assumption_overrides["tariff.vat_rate"] = vat_percent / 100

        if demand_charge != float(defaults["tariff"]["demand_charge_bdt"]):
            assumption_overrides["tariff.demand_charge_bdt"] = demand_charge

        if area_per_kw != float(defaults["roof"]["area_per_kw_sqm"]):
            assumption_overrides["roof.area_per_kw_sqm"] = area_per_kw

    language = st.selectbox(
        "Report language",
        ["English", "বাংলা"],
    )

    assess_clicked = st.button(
        "Assess Solar Potential",
        use_container_width=True,
    )

    st.divider()

    if st.button(
        "Clear Conversation",
        use_container_width=True,
    ):
        st.session_state["chat_history"] = []
        st.session_state["agent_messages"] = []
        st.rerun()


# --------------------------------------------------
# RUN SOLAR ASSESSMENT
# --------------------------------------------------

if assess_clicked:
    if not location.strip():
        st.warning("Please enter your location.")

    elif monthly_bill <= 0:
        st.warning(
            "Please enter a monthly bill greater than zero."
        )

    else:
        try:
            with st.spinner("Calculating solar potential..."):
                result = assess_solar_feasibility(
                    monthly_bill_bdt=monthly_bill,
                    roof_area_sqm=roof_area,
                    location=location,
                    needs_battery=needs_battery,
                    backup_load_kw=backup_load,
                    backup_hours=backup_hours,
                    overrides=assumption_overrides or None,
                )

            report_language = (
                "bn" if language == "বাংলা" else "en"
            )

            report = generate_solar_report(
                result,
                language=report_language,
            )

            # Save the assessment result and generated report.
            st.session_state["assessment"] = result
            st.session_state["report"] = report
            st.session_state["report_pdf"] = None  # rebuild for new data

            # Save the exact inputs used for this assessment.
            st.session_state["assessment_inputs"] = {
                "location": location,
                "monthly_bill_bdt": monthly_bill,
                "roof_area_sqm": roof_area,
                "needs_battery": needs_battery,
                "backup_load_kw": (
                    backup_load if needs_battery else None
                ),
                "backup_hours": (
                    backup_hours if needs_battery else None
                ),
            }

        except (ValueError, RuntimeError) as error:
            st.error(str(error))


# --------------------------------------------------
# DISPLAY SOLAR ASSESSMENT
# --------------------------------------------------

if st.session_state["assessment"] is not None:
    result = st.session_state["assessment"]
    report = st.session_state["report"]

    st.subheader("Your Solar Assessment")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Solar Capacity",
        f"{result['solar_capacity_kw']} kW",
    )

    col2.metric(
        "Monthly Generation",
        f"{result['generation']['monthly_generation_kwh']} kWh",
    )

    col3.metric(
        "Estimated Cost",
        f"৳{result['cost']['total_cost_bdt']:,.0f}",
    )

    # --------------------------------------------------
    # DATA WARNINGS (unverified or out-of-date assumptions)
    # --------------------------------------------------

    assumptions = result.get("assumptions") or {}
    data_warnings = assumptions.get("warnings") or []

    if data_warnings:
        st.warning(
            "**Check these assumptions before relying on the numbers:**\n\n"
            + "\n".join(f"- {warning}" for warning in data_warnings)
            + "\n\nYou can enter your own values under "
            "*Advanced: use your own prices* in the sidebar."
        )

    # --------------------------------------------------
    # SAVINGS AND PAYBACK
    # --------------------------------------------------

    savings = result.get("savings")
    sizing = result.get("sizing")

    if savings:
        st.subheader("Savings and Payback")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Monthly Savings",
            f"৳{savings['monthly_savings_bdt']:,.0f}",
        )

        col2.metric(
            "Bill After Solar",
            f"৳{savings['monthly_bill_after_bdt']:,.0f}",
            delta=f"-৳{savings['monthly_savings_bdt']:,.0f}",
            delta_color="inverse",
        )

        payback = savings.get("payback_years")

        col3.metric(
            "Simple Payback",
            f"{payback:,.1f} years" if payback is not None else "N/A",
        )

        if sizing and sizing["limiting_factor"] == "roof_area":
            st.info(
                "Your roof can hold "
                f"{sizing['roof_limit_kw']} kW, which is less than the "
                f"{sizing['demand_based_kw']} kW needed to cover your "
                "average consumption, so the system is sized to the roof."
            )
        elif sizing:
            st.info(
                f"The system is sized to cover your average consumption "
                f"({sizing['demand_based_kw']} kW). Your roof could hold "
                f"up to {sizing['roof_limit_kw']} kW."
            )

        if savings.get("payback_years_including_battery") is not None:
            st.caption(
                "Payback with the backup battery included: "
                f"{savings['payback_years_including_battery']:,.1f} years. "
                "A backup battery does not reduce your bill."
            )

    # --------------------------------------------------
    # ENERGY ASSESSMENT
    # --------------------------------------------------

    energy = result.get("energy_assessment")

    if energy:
        st.subheader("Energy Assessment")

        generation = result["generation"][
            "monthly_generation_kwh"
        ]

        consumption = result["electricity"][
            "monthly_consumption_kwh"
        ]

        col1, col2 = st.columns(2)

        col1.metric(
            "Estimated Monthly Solar Generation",
            f"{generation:,.2f} kWh",
        )

        col2.metric(
            "Estimated Monthly Consumption",
            f"{consumption:,.2f} kWh",
        )

        if energy["status"] == "potential_surplus":
            st.success(
                "Estimated monthly surplus: "
                f"{energy['monthly_surplus_kwh']:,.2f} kWh"
            )

        elif energy["status"] == "potential_shortfall":
            st.warning(
                "Estimated monthly shortfall: "
                f"{energy['monthly_shortfall_kwh']:,.2f} kWh"
            )

        else:
            st.info(
                "Estimated solar generation approximately "
                "matches household consumption."
            )

    # --------------------------------------------------
    # DETAILED FEASIBILITY REPORT
    # --------------------------------------------------

    st.subheader("Feasibility Report")
    st.markdown(report)

    # --------------------------------------------------
    # PDF DOWNLOAD
    # --------------------------------------------------

    # Build the PDF once per assessment and reuse the same bytes on every
    # rerun. Rebuilding it on each chat message can make the browser
    # download the file again automatically.
    if st.session_state["report_pdf"] is None:
        try:
            st.session_state["report_pdf"] = generate_solar_report_pdf(
                report=report,
                assessment=result,
                assessment_inputs=(
                    st.session_state["assessment_inputs"]
                ),
            )

        except (ValueError, RuntimeError, OSError) as error:
            st.error(
                f"Could not generate the PDF report: {error}"
            )

    if st.session_state["report_pdf"] is not None:
        # on_click="ignore" stops a download click from rerunning the
        # script. It needs Streamlit 1.43 or newer.
        _version = tuple(
            int(part)
            for part in st.__version__.split(".")[:2]
            if part.isdigit()
        )
        _download_options = (
            {"on_click": "ignore"} if _version >= (1, 43) else {}
        )

        st.download_button(
            label="📄 Download Report (PDF)",
            data=st.session_state["report_pdf"],
            file_name="bangla_solar_report.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="download_solar_report_pdf",
            **_download_options,
        )

    # --------------------------------------------------
    # ASSUMPTIONS AND LIMITATIONS
    # --------------------------------------------------

    with st.expander("View assumptions and limitations"):
        st.markdown("**Assumptions used**")

        overrides_used = assumptions.get("overrides") or {}

        st.table(
            [
                {
                    "Assumption": key,
                    "Value": str(value),
                    "Source": (
                        "your override"
                        if key in overrides_used
                        else "data/assumptions.json"
                    ),
                }
                for key, value in (assumptions.get("values") or {}).items()
            ]
        )

        for name, source in (assumptions.get("sources") or {}).items():
            link = (
                f" ([source]({source['source_url']}))"
                if source.get("source_url")
                else ""
            )
            st.write(
                f"- {source['label']}: "
                f"as of {source.get('as_of') or 'n/a'}, "
                f"{'verified' if source.get('verified') else 'unverified'}"
                f"{link}"
            )

        st.markdown("**Limitations**")

        for limitation in result.get("limitations", []):
            st.write(f"- {limitation}")


# --------------------------------------------------
# CHAT INTERFACE
# --------------------------------------------------

st.divider()
st.subheader("Ask Bangla Solar AI")

# Display previous conversation.
for message in st.session_state["chat_history"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input(
    "Ask about solar panels, generation, costs, or batteries..."
)


# --------------------------------------------------
# CHAT: LANGGRAPH AGENT + MEMORY + TOOL TRACE
# --------------------------------------------------

if user_input:
    # Save and display the user's message.
    st.session_state["chat_history"].append(
        {
            "role": "user",
            "content": user_input,
        }
    )

    with st.chat_message("user"):
        st.markdown(user_input)

    # Include previous LangChain messages for agent memory.
    current_messages = (
        st.session_state["agent_messages"]
        + [HumanMessage(content=user_input)]
    )

    try:
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                agent_result = run_solar_agent(
                    current_messages,
                    assessment_context=build_assessment_context(
                        st.session_state["assessment"],
                        st.session_state["assessment_inputs"],
                    ),
                )

            # Preserve agent messages and tool interactions.
            st.session_state["agent_messages"] = (
                current_messages + agent_result["messages"]
            )

            answer = agent_result["answer"]

            if answer:
                st.markdown(answer)
            else:
                answer = (
                    "The agent finished without returning "
                    "a text response. Check the execution trace."
                )
                st.warning(answer)

            # --------------------------------------------------
            # AGENT EXECUTION TRACE
            # --------------------------------------------------

            tool_calls = agent_result["tool_calls"]
            tool_results = agent_result["tool_results"]
            node_events = agent_result["node_events"]

            with st.expander(
                f"🔧 Agent Execution Trace "
                f"({len(tool_calls)} tool calls)",
                expanded=True,
            ):
                st.write("**Graph nodes executed:**")
                st.write(" → ".join(node_events))

                if not tool_calls:
                    st.info(
                        "The agent did not request any tools "
                        "for this message."
                    )

                for index, call in enumerate(
                    tool_calls,
                    start=1,
                ):
                    st.markdown(
                        f"### {index}. `{call['name']}`"
                    )

                    st.caption("Arguments sent to the tool")
                    st.json(call["args"])

                    matching_results = [
                        item
                        for item in tool_results
                        if (
                            call["id"] is not None
                            and item["tool_call_id"] == call["id"]
                        )
                    ]

                    for item in matching_results:
                        st.caption("Tool result")
                        st.code(item["result"])

                # Find results without a matching tool-call ID.
                matched_ids = {
                    item["tool_call_id"]
                    for call in tool_calls
                    for item in tool_results
                    if (
                        call["id"] is not None
                        and item["tool_call_id"] == call["id"]
                    )
                }

                unmatched_results = [
                    item
                    for item in tool_results
                    if item["tool_call_id"] not in matched_ids
                ]

                if unmatched_results:
                    st.markdown("### Other tool results")

                    for item in unmatched_results:
                        st.write(f"Tool: `{item['name']}`")
                        st.code(item["result"])

        # Save the assistant response in the visible chat history.
        st.session_state["chat_history"].append(
            {
                "role": "assistant",
                "content": answer,
            }
        )

    except Exception as error:
        st.error(f"Agent request failed: {error}")
