import altair as alt
import pandas as pd
import streamlit as st
from langchain_core.messages import HumanMessage

from services.agent_service import build_assessment_context, run_solar_agent
from services.i18n import (
    digits,
    fmt,
    month_name,
    t,
    translate_limitation,
)
from services.report_service import (
    generate_solar_report,
    generate_solar_report_pdf,
)
from services.solar_engine import assess_solar_feasibility
from tools.config import AssumptionsError, resolve_assumptions


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Bangla Solar AI",
    page_icon="☀️",
    layout="wide",
)

# Full-width widgets: Streamlit 1.50+ uses width="stretch" and deprecates
# use_container_width, which older versions still need.
_ST_VERSION = tuple(
    int(part) for part in st.__version__.split(".")[:2] if part.isdigit()
)
STRETCH = (
    {"width": "stretch"}
    if _ST_VERSION >= (1, 50)
    else {"use_container_width": True}
)

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

for name, default in {
    "chat_history": [],
    "agent_messages": [],
    "assessment": None,
    "assessment_inputs": None,
    "report_pdf": {},  # language -> PDF bytes, built once per assessment
}.items():
    if name not in st.session_state:
        st.session_state[name] = default


# --------------------------------------------------
# LANGUAGE (drives the whole UI, the report and the PDF)
# --------------------------------------------------

with st.sidebar:
    language_choice = st.selectbox(
        "Language / ভাষা",
        ["English", "বাংলা"],
        key="ui_language",
    )

lang = "bn" if language_choice == "বাংলা" else "en"

st.title(t(lang, "app_title"))
st.caption(t(lang, "app_caption"))


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def localized_warning(item: dict) -> str:
    """Word a structured data warning in the current language."""

    use_bn = lang == "bn"
    key = {
        "unverified": "warn_unverified",
        "estimate": "warn_estimate",
        "stale": "warn_stale",
        "bad_date": "warn_bad_date",
    }[item["code"]]

    text = t(
        lang,
        key,
        label=item["label_bn"] if use_bn else item["label"],
        note=item["note_bn"] if use_bn else item["note"],
        age=item.get("age_days", ""),
        as_of=item.get("as_of") or "",
    )

    return digits(lang, text)


def localized_error(error: Exception) -> str:
    """Translate the most common engine errors; others stay as they are."""

    message = str(error)
    prefix = "Could not find the location:"

    if message.startswith(prefix):
        return t(
            lang,
            "err_location_not_found",
            location=message[len(prefix):].strip(),
        )

    return message


def format_assumption(key: str, value) -> str:
    """Show one stored assumption in the current language."""

    if key == "tariff.slabs":
        parts = []

        for slab in value:
            if slab["up_to_kwh"] is None:
                parts.append(
                    t(lang, "slab_above", rate=slab["rate_bdt"])
                )
            else:
                parts.append(
                    t(
                        lang,
                        "slab_upto",
                        n=slab["up_to_kwh"],
                        rate=slab["rate_bdt"],
                    )
                )

        return "; ".join(parts)

    if value is None:
        return t(lang, "na")

    if isinstance(value, bool):
        return t(lang, "yes" if value else "no")

    if isinstance(value, list):
        return digits(lang, ", ".join(str(v) for v in value))

    return digits(lang, value)


# --------------------------------------------------
# SIDEBAR: SOLAR ASSESSMENT
# --------------------------------------------------

assumption_overrides = {}

try:
    defaults = resolve_assumptions()
except AssumptionsError as error:
    defaults = None
    st.sidebar.error(
        t(lang, "err_assumptions_file", error=error)
    )

with st.sidebar:
    st.header(t(lang, "sidebar_header"))

    location = st.text_input(
        t(lang, "location"),
        placeholder=t(lang, "location_ph"),
        key="location",
    )

    monthly_bill = st.number_input(
        t(lang, "monthly_bill"),
        min_value=0.0,
        value=3000.0,
        step=100.0,
        key="monthly_bill",
    )

    roof_area = st.number_input(
        t(lang, "roof_area"),
        min_value=1.0,
        value=50.0,
        step=5.0,
        key="roof_area",
    )

    default_load = (
        float(defaults["tariff"]["sanctioned_load_kw"]) if defaults else 2.0
    )

    sanctioned_load = st.number_input(
        t(lang, "sanctioned_load"),
        min_value=0.1,
        max_value=50.0,
        value=default_load,
        step=0.5,
        help=t(lang, "sanctioned_load_help"),
        key="sanctioned_load",
    )

    needs_battery = st.checkbox(
        t(lang, "needs_battery"),
        key="needs_battery",
    )

    backup_load = 0.5
    backup_hours = 4.0

    if needs_battery:
        backup_load = st.number_input(
            t(lang, "backup_load"),
            min_value=0.1,
            value=0.5,
            step=0.1,
            key="backup_load",
        )

        backup_hours = st.number_input(
            t(lang, "backup_hours"),
            min_value=1.0,
            value=4.0,
            step=1.0,
            key="backup_hours",
        )

    use_net_metering = st.checkbox(
        t(lang, "net_metering"),
        value=(
            bool(defaults["net_metering"]["enabled_by_default"])
            if defaults
            else True
        ),
        help=t(lang, "net_metering_help"),
        key="use_net_metering",
    )

    # Defaults come from data/assumptions.json. Only values the user
    # changes are sent as overrides.
    if defaults is not None:
        with st.expander(t(lang, "advanced")):
            st.caption(t(lang, "advanced_caption"))

            solar_cost = st.number_input(
                t(lang, "solar_cost"),
                min_value=1.0,
                value=float(defaults["costs"]["solar_cost_per_kw_bdt"]),
                step=5000.0,
                key="solar_cost",
            )

            battery_cost = st.number_input(
                t(lang, "battery_cost"),
                min_value=1.0,
                value=float(defaults["costs"]["battery_cost_per_kwh_bdt"]),
                step=1000.0,
                key="battery_cost",
            )

            vat_percent = st.number_input(
                t(lang, "vat_percent"),
                min_value=0.0,
                max_value=100.0,
                value=float(defaults["tariff"]["vat_rate"]) * 100,
                step=0.5,
                key="vat_percent",
            )

            surplus_rate = st.number_input(
                t(lang, "surplus_rate"),
                min_value=0.0,
                max_value=100.0,
                value=float(
                    defaults["net_metering"]["standard_surplus_rate_bdt_per_kwh"]
                ),
                step=0.5,
                key="surplus_rate",
            )

            area_per_kw = st.number_input(
                t(lang, "area_per_kw"),
                min_value=2.0,
                max_value=30.0,
                value=float(defaults["roof"]["area_per_kw_sqm"]),
                step=0.5,
                key="area_per_kw",
            )

        changes = {
            "tariff.sanctioned_load_kw": (
                sanctioned_load,
                float(defaults["tariff"]["sanctioned_load_kw"]),
            ),
            "costs.solar_cost_per_kw_bdt": (
                solar_cost,
                float(defaults["costs"]["solar_cost_per_kw_bdt"]),
            ),
            "costs.battery_cost_per_kwh_bdt": (
                battery_cost,
                float(defaults["costs"]["battery_cost_per_kwh_bdt"]),
            ),
            "tariff.vat_rate": (
                vat_percent / 100,
                float(defaults["tariff"]["vat_rate"]),
            ),
            "net_metering.standard_surplus_rate_bdt_per_kwh": (
                surplus_rate,
                float(
                    defaults["net_metering"]["standard_surplus_rate_bdt_per_kwh"]
                ),
            ),
            "roof.area_per_kw_sqm": (
                area_per_kw,
                float(defaults["roof"]["area_per_kw_sqm"]),
            ),
        }

        for override_key, (chosen, stored) in changes.items():
            if abs(chosen - stored) > 1e-9:
                assumption_overrides[override_key] = chosen

    assess_clicked = st.button(
        t(lang, "assess_btn"),
        **STRETCH,
        disabled=defaults is None,
        key="assess_button",
    )

    st.divider()

    if st.button(
        t(lang, "clear_btn"),
        **STRETCH,
        key="clear_button",
    ):
        st.session_state["chat_history"] = []
        st.session_state["agent_messages"] = []
        st.rerun()


# --------------------------------------------------
# RUN SOLAR ASSESSMENT
# --------------------------------------------------

if assess_clicked:
    if not location.strip():
        st.warning(t(lang, "warn_enter_location"))

    elif monthly_bill <= 0:
        st.warning(t(lang, "warn_bill_positive"))

    else:
        try:
            with st.spinner(t(lang, "spinner_calc")):
                result = assess_solar_feasibility(
                    monthly_bill_bdt=monthly_bill,
                    roof_area_sqm=roof_area,
                    location=location,
                    needs_battery=needs_battery,
                    backup_load_kw=backup_load,
                    backup_hours=backup_hours,
                    overrides=assumption_overrides or None,
                    use_net_metering=use_net_metering,
                )

            st.session_state["assessment"] = result

            # Save the exact inputs used for this assessment.
            st.session_state["assessment_inputs"] = {
                "location": location,
                "monthly_bill_bdt": monthly_bill,
                "roof_area_sqm": roof_area,
                "needs_battery": needs_battery,
                "backup_load_kw": backup_load if needs_battery else None,
                "backup_hours": backup_hours if needs_battery else None,
            }

            # New numbers: the cached PDFs are out of date.
            st.session_state["report_pdf"] = {}

        except (ValueError, RuntimeError) as error:
            st.error(localized_error(error))


# --------------------------------------------------
# DISPLAY SOLAR ASSESSMENT
# --------------------------------------------------

if st.session_state["assessment"] is not None:
    result = st.session_state["assessment"]

    # The report text is cheap to build, so it always follows the
    # current language without recalculating anything.
    report = generate_solar_report(result, language=lang)

    assumptions = result.get("assumptions") or {}
    savings = result.get("savings") or {}
    sizing = result.get("sizing") or {}
    net_info = result.get("net_metering_info") or {}

    st.subheader(t(lang, "assess_header"))

    col1, col2, col3 = st.columns(3)

    col1.metric(
        t(lang, "m_capacity"),
        t(lang, "kw", n=fmt(lang, result["solar_capacity_kw"], 2)),
    )

    col2.metric(
        t(lang, "m_monthly_gen"),
        t(
            lang,
            "kwh",
            n=fmt(lang, result["generation"]["monthly_generation_kwh"], 0),
        ),
    )

    col3.metric(
        t(lang, "m_cost"),
        f"৳{fmt(lang, result['cost']['total_cost_bdt'], 0)}",
    )

    # --------------------------------------------------
    # DATA WARNINGS (unverified, estimated or out-of-date assumptions)
    # --------------------------------------------------

    warning_items = assumptions.get("warning_items") or []

    if warning_items:
        st.warning(
            f"**{t(lang, 'check_title')}**\n\n"
            + "\n".join(f"- {localized_warning(i)}" for i in warning_items)
            + f"\n\n{t(lang, 'check_hint')}"
        )

    # --------------------------------------------------
    # SAVINGS AND PAYBACK
    # --------------------------------------------------

    if savings:
        st.subheader(t(lang, "savings_header"))

        col1, col2, col3 = st.columns(3)

        col1.metric(
            t(lang, "m_monthly_savings"),
            f"৳{fmt(lang, savings['monthly_savings_bdt'], 0)}",
        )

        col2.metric(
            t(lang, "m_bill_after"),
            f"৳{fmt(lang, savings['monthly_bill_after_bdt'], 0)}",
            delta=f"-৳{fmt(lang, savings['monthly_savings_bdt'], 0)}",
            delta_color="inverse",
        )

        payback = savings.get("payback_years")

        col3.metric(
            t(lang, "m_payback"),
            t(lang, "years", n=fmt(lang, payback, 1))
            if payback is not None
            else t(lang, "na"),
        )

        if sizing.get("limiting_factor") == "roof_area":
            st.info(
                t(
                    lang,
                    "info_roof_limited",
                    roof=fmt(lang, sizing["roof_limit_kw"], 2),
                    demand=fmt(lang, sizing["demand_based_kw"], 2),
                )
            )
        elif sizing:
            st.info(
                t(
                    lang,
                    "info_consumption_sized",
                    roof=fmt(lang, sizing["roof_limit_kw"], 2),
                    demand=fmt(lang, sizing["demand_based_kw"], 2),
                )
            )

        if savings.get("payback_years_including_battery") is not None:
            st.caption(
                t(
                    lang,
                    "battery_payback",
                    n=fmt(lang, savings["payback_years_including_battery"], 1),
                )
            )

        # Net metering status
        if net_info:
            if not net_info["enabled"]:
                st.info(t(lang, "nm_off"))
            elif net_info["incentive_eligible"]:
                st.success(
                    t(
                        lang,
                        "nm_on_incentive",
                        rate=fmt(lang, net_info["surplus_rate_bdt_per_kwh"], 2),
                        deadline=digits(lang, net_info["incentive_install_deadline"]),
                        until=digits(lang, net_info["incentive_valid_until"]),
                    )
                )
            else:
                st.info(
                    t(
                        lang,
                        "nm_on_standard",
                        rate=fmt(lang, net_info["surplus_rate_bdt_per_kwh"], 2),
                    )
                )

            if net_info["enabled"] and not net_info["within_sanctioned_load"]:
                st.warning(
                    t(
                        lang,
                        "nm_load_warning",
                        capacity=fmt(lang, result["solar_capacity_kw"], 2),
                        allowed=fmt(lang, net_info["max_net_metered_kw"], 2),
                        load=fmt(lang, net_info["sanctioned_load_kw"], 2),
                    )
                )

    # --------------------------------------------------
    # MONTH BY MONTH
    # --------------------------------------------------

    monthly = result.get("monthly") or []

    if monthly:
        st.subheader(t(lang, "monthly_header"))
        st.caption(t(lang, "monthly_caption"))

        order = [month_name(lang, row["month"]) for row in monthly]
        generation_name = t(lang, "series_generation")
        consumption_name = t(lang, "series_consumption")
        before_name = t(lang, "series_before")
        after_name = t(lang, "series_after")

        energy_data = pd.DataFrame(
            [
                {"month": m, "series": generation_name, "value": r["generation_kwh"]}
                for m, r in zip(order, monthly)
            ]
            + [
                {"month": m, "series": consumption_name, "value": r["consumption_kwh"]}
                for m, r in zip(order, monthly)
            ]
        )

        bill_data = pd.DataFrame(
            [
                {"month": m, "series": before_name, "value": r["bill_before_bdt"]}
                for m, r in zip(order, monthly)
            ]
            + [
                {"month": m, "series": after_name, "value": r["bill_after_bdt"]}
                for m, r in zip(order, monthly)
            ]
        )

        chart_left, chart_right = st.columns(2)

        with chart_left:
            st.markdown(f"**{t(lang, 'chart_energy')}**")
            st.altair_chart(
                alt.Chart(energy_data)
                .mark_line(point=True)
                .encode(
                    x=alt.X("month:N", sort=order, title=None),
                    y=alt.Y("value:Q", title=None),
                    color=alt.Color("series:N", title=None),
                ),
                **STRETCH,
            )

        with chart_right:
            st.markdown(f"**{t(lang, 'chart_bills')}**")
            st.altair_chart(
                alt.Chart(bill_data)
                .mark_bar()
                .encode(
                    x=alt.X("month:N", sort=order, title=None),
                    xOffset="series:N",
                    y=alt.Y("value:Q", title=None),
                    color=alt.Color("series:N", title=None),
                ),
                **STRETCH,
            )

        st.dataframe(
            pd.DataFrame(
                {
                    t(lang, "col_month"): order,
                    t(lang, "col_consumption"): [fmt(lang, r["consumption_kwh"], 0) for r in monthly],
                    t(lang, "col_generation"): [fmt(lang, r["generation_kwh"], 0) for r in monthly],
                    t(lang, "col_billed"): [fmt(lang, r["billed_kwh"], 0) for r in monthly],
                    t(lang, "col_credit"): [fmt(lang, r["credit_balance_kwh"], 0) for r in monthly],
                    t(lang, "col_before"): [fmt(lang, r["bill_before_bdt"], 0) for r in monthly],
                    t(lang, "col_after"): [fmt(lang, r["bill_after_bdt"], 0) for r in monthly],
                    t(lang, "col_payout"): [fmt(lang, r["payout_bdt"], 0) for r in monthly],
                    t(lang, "col_savings"): [fmt(lang, r["savings_bdt"], 0) for r in monthly],
                }
            ),
            hide_index=True,
            **STRETCH,
        )

    # --------------------------------------------------
    # ENERGY ASSESSMENT
    # --------------------------------------------------

    energy = result.get("energy_assessment")

    if energy:
        st.subheader(t(lang, "energy_header"))

        col1, col2 = st.columns(2)

        col1.metric(
            t(lang, "m_est_gen"),
            t(
                lang,
                "kwh",
                n=fmt(lang, result["generation"]["monthly_generation_kwh"], 2),
            ),
        )

        col2.metric(
            t(lang, "m_est_cons"),
            t(
                lang,
                "kwh",
                n=fmt(lang, result["electricity"]["monthly_consumption_kwh"], 2),
            ),
        )

        if energy["status"] == "potential_surplus":
            st.success(
                t(lang, "energy_surplus", v=fmt(lang, energy["monthly_surplus_kwh"], 2))
            )
        elif energy["status"] == "potential_shortfall":
            st.warning(
                t(lang, "energy_shortfall", v=fmt(lang, energy["monthly_shortfall_kwh"], 2))
            )
        else:
            st.info(t(lang, "energy_balanced"))

    # --------------------------------------------------
    # DETAILED FEASIBILITY REPORT
    # --------------------------------------------------

    st.subheader(t(lang, "report_header"))
    st.markdown(report)

    # --------------------------------------------------
    # PDF DOWNLOAD
    # --------------------------------------------------

    # Build each language's PDF once per assessment and reuse the same
    # bytes on every rerun. Rebuilding it on each chat message can make
    # the browser download the file again automatically.
    pdf_cache = st.session_state["report_pdf"]

    if lang not in pdf_cache:
        try:
            pdf_cache[lang] = generate_solar_report_pdf(
                report=report,
                assessment=result,
                assessment_inputs=st.session_state["assessment_inputs"],
                language=lang,
            )
        except (ValueError, RuntimeError, OSError) as error:
            st.error(t(lang, "pdf_err", error=error))

    if lang in pdf_cache:
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
            label=t(lang, "pdf_btn"),
            data=pdf_cache[lang],
            file_name="bangla_solar_report.pdf",
            mime="application/pdf",
            **STRETCH,
            key="download_solar_report_pdf",
            **_download_options,
        )

    # --------------------------------------------------
    # ASSUMPTIONS AND LIMITATIONS
    # --------------------------------------------------

    with st.expander(t(lang, "assumptions_expander")):
        st.markdown(f"**{t(lang, 'assumptions_used')}**")

        overrides_used = assumptions.get("overrides") or {}

        st.dataframe(
            pd.DataFrame(
                [
                    {
                        t(lang, "col_assumption"): t(lang, f"a.{key}"),
                        t(lang, "col_value"): format_assumption(key, value),
                        t(lang, "col_source"): t(
                            lang,
                            "src_override" if key in overrides_used else "src_file",
                        ),
                    }
                    for key, value in (assumptions.get("values") or {}).items()
                ]
            ),
            hide_index=True,
            **STRETCH,
        )

        for source in (assumptions.get("sources") or {}).values():
            use_bn = lang == "bn"
            status = (
                t(lang, "status_unverified")
                if source.get("verified") is False
                else t(lang, "status_verified")
            )

            if source.get("estimate"):
                status += f", {t(lang, 'status_estimate')}"

            link = (
                f" ([{t(lang, 'source_word')}]({source['source_url']}))"
                if source.get("source_url")
                else ""
            )

            st.write(
                "- "
                + digits(
                    lang,
                    t(
                        lang,
                        "source_line",
                        label=source["label_bn"] if use_bn else source["label"],
                        as_of=source.get("as_of") or t(lang, "na"),
                        status=status,
                        link=link,
                    ),
                )
            )

            note = source["note_bn"] if use_bn else source.get("note")

            if note:
                st.caption(digits(lang, note))

        st.markdown(f"**{t(lang, 'limitations_header')}**")

        for limitation in result.get("limitations", []):
            st.write(f"- {translate_limitation(lang, limitation)}")


# --------------------------------------------------
# CHAT INTERFACE
# --------------------------------------------------

st.divider()
st.subheader(t(lang, "chat_header"))

# Display previous conversation.
for message in st.session_state["chat_history"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_input = st.chat_input(t(lang, "chat_placeholder"))


# --------------------------------------------------
# CHAT: LANGGRAPH AGENT + MEMORY + TOOL TRACE
# --------------------------------------------------

if user_input:
    # Save and display the user's message.
    st.session_state["chat_history"].append(
        {"role": "user", "content": user_input}
    )

    with st.chat_message("user"):
        st.markdown(user_input)

    # Include previous LangChain messages for agent memory.
    current_messages = st.session_state["agent_messages"] + [
        HumanMessage(content=user_input)
    ]

    try:
        with st.chat_message("assistant"):
            with st.spinner("..."):
                agent_result = run_solar_agent(
                    current_messages,
                    assessment_context=build_assessment_context(
                        st.session_state["assessment"],
                        st.session_state["assessment_inputs"],
                        language=lang,
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
                answer = t(lang, "agent_no_text")
                st.warning(answer)

            # --------------------------------------------------
            # AGENT EXECUTION TRACE
            # --------------------------------------------------

            tool_calls = agent_result["tool_calls"]
            tool_results = agent_result["tool_results"]
            node_events = agent_result["node_events"]

            with st.expander(
                t(lang, "trace_title", n=len(tool_calls)),
                expanded=True,
            ):
                st.write(t(lang, "trace_nodes"))
                st.write(" → ".join(node_events))

                if not tool_calls:
                    st.info(t(lang, "trace_none"))

                for index, call in enumerate(tool_calls, start=1):
                    st.markdown(f"### {index}. `{call['name']}`")

                    st.caption(t(lang, "trace_args"))
                    st.json(call["args"])

                    for item in tool_results:
                        if (
                            call["id"] is not None
                            and item["tool_call_id"] == call["id"]
                        ):
                            st.caption(t(lang, "trace_result"))
                            st.code(item["result"])

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
                    st.markdown(f"### {t(lang, 'trace_other')}")

                    for item in unmatched_results:
                        st.write(t(lang, "trace_tool", name=item["name"]))
                        st.code(item["result"])

        # Save the assistant response in the visible chat history.
        st.session_state["chat_history"].append(
            {"role": "assistant", "content": answer}
        )

    except Exception as error:
        st.error(t(lang, "agent_fail", error=error))
