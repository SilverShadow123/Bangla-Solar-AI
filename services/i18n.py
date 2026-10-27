"""English and Bangla text for the whole app (UI, report labels, PDF).

Use t(lang, key, **values) for text and fmt(lang, number, decimals) for
numbers. In Bangla mode, digits are shown as Bengali digits (০-৯).
"""

DEFAULT_LANGUAGE = "en"

BN_DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")

MONTH_NAMES = {
    "en": [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ],
    "bn": [
        "জানুয়ারি", "ফেব্রুয়ারি", "মার্চ", "এপ্রিল", "মে", "জুন",
        "জুলাই", "আগস্ট", "সেপ্টেম্বর", "অক্টোবর", "নভেম্বর", "ডিসেম্বর",
    ],
}


def digits(lang: str, text) -> str:
    """Convert 0-9 to Bengali digits when the language is Bangla."""

    text = str(text)
    return text.translate(BN_DIGITS) if lang == "bn" else text


def fmt(lang: str, value, decimals: int = 0) -> str:
    """Format a number with thousands separators in the chosen language."""

    if value is None:
        return t(lang, "na")

    try:
        return digits(lang, f"{float(value):,.{decimals}f}")
    except (TypeError, ValueError):
        return str(value)


def month_name(lang: str, month: int) -> str:
    return MONTH_NAMES.get(lang, MONTH_NAMES["en"])[month - 1]


TEXT = {
    "en": {
        # ----- general -----
        "language_label": "Language / ভাষা",
        "app_title": "☀️ Bangla Solar AI",
        "app_caption": "Check your rooftop solar feasibility in Bangla or English",
        "na": "N/A",
        "yes": "Yes",
        "no": "No",
        "years": "{n} years",
        "kwh": "{n} kWh",
        "kw": "{n} kW",

        # ----- sidebar -----
        "sidebar_header": "Solar Assessment",
        "location": "Location",
        "location_ph": "e.g. Barishal, Bangladesh",
        "monthly_bill": "Monthly electricity bill (BDT)",
        "roof_area": "Roof area (m²)",
        "sanctioned_load": "Sanctioned load (kW)",
        "sanctioned_load_help": "Printed on your electricity bill. It sets your fixed demand charge and the largest net-metered system allowed.",
        "needs_battery": "I need battery backup",
        "backup_load": "Backup load (kW)",
        "backup_hours": "Backup duration (hours)",
        "net_metering": "I will use net metering",
        "net_metering_help": "Surplus power is credited and paid under the Net Metering Guidelines 2025.",
        "advanced": "Advanced: use your own prices",
        "advanced_caption": "Defaults come from data/assumptions.json. Change a value to use your own installer quote or the figures on your bill.",
        "solar_cost": "Solar cost per kW (BDT)",
        "battery_cost": "Battery cost per kWh (BDT)",
        "vat_percent": "VAT on bill (%)",
        "surplus_rate": "Surplus payment rate (BDT per unit)",
        "area_per_kw": "Roof area per kW of panels (m²)",
        "assess_btn": "Assess Solar Potential",
        "clear_btn": "Clear Conversation",

        # ----- messages -----
        "warn_enter_location": "Please enter your location.",
        "warn_bill_positive": "Please enter a monthly bill greater than zero.",
        "spinner_calc": "Calculating solar potential...",
        "err_assumptions_file": "Assumptions file problem: {error}",
        "err_location_not_found": "Could not find the location: {location}",

        # ----- results -----
        "assess_header": "Your Solar Assessment",
        "m_capacity": "Solar Capacity",
        "m_monthly_gen": "Monthly Generation",
        "m_cost": "Estimated Cost",
        "check_title": "Check these assumptions before relying on the numbers:",
        "check_hint": "You can enter your own values under “Advanced: use your own prices” in the sidebar.",
        "warn_unverified": "Unverified: {label}. {note}",
        "warn_estimate": "Market estimate: {label}. {note}",
        "warn_stale": "Out of date: {label} is {age} days old (as of {as_of}). Please check the source.",
        "warn_bad_date": "Unreadable date for {label}. Use YYYY-MM-DD.",

        "savings_header": "Savings and Payback",
        "m_monthly_savings": "Average Monthly Savings",
        "m_bill_after": "Average Bill After Solar",
        "m_payback": "Simple Payback",
        "info_roof_limited": "Your roof can hold {roof} kW, which is less than the {demand} kW needed to cover your average consumption, so the system is sized to the roof.",
        "info_consumption_sized": "The system is sized to cover your average consumption ({demand} kW). Your roof could hold up to {roof} kW.",
        "battery_payback": "Payback with the backup battery included: {n} years. A backup battery does not reduce your bill.",
        "nm_on_standard": "Net metering is on. Surplus power is paid at about ৳{rate} per unit (estimated bulk rate).",
        "nm_on_incentive": "Net metering is on, and your battery-backed system qualifies for the ৳{rate} per unit surplus incentive (installed by {deadline}, paid until {until}).",
        "nm_off": "Net metering is off: surplus power is assumed to have no value.",
        "nm_load_warning": "This {capacity} kW system is larger than the {allowed} kW net metering allows for your {load} kW sanctioned load. You may need to apply for a load increase.",

        "monthly_header": "Month by Month",
        "monthly_caption": "Generation follows the PVGIS typical-weather profile. Credit from sunny months is carried forward and settled in the settlement months.",
        "chart_energy": "Solar generation vs your consumption (kWh)",
        "chart_bills": "Bill before vs after solar (BDT)",
        "series_generation": "Solar generation",
        "series_consumption": "Your consumption",
        "series_before": "Bill before solar",
        "series_after": "Bill after solar",
        "col_month": "Month",
        "col_consumption": "Use (kWh)",
        "col_generation": "Solar (kWh)",
        "col_billed": "Billed units",
        "col_credit": "Credit (kWh)",
        "col_before": "Bill before (৳)",
        "col_after": "Bill after (৳)",
        "col_payout": "Surplus paid (৳)",
        "col_savings": "Savings (৳)",

        "energy_header": "Energy Assessment",
        "m_est_gen": "Estimated Monthly Solar Generation",
        "m_est_cons": "Estimated Monthly Consumption",
        "energy_surplus": "Estimated average monthly surplus: {v} kWh",
        "energy_shortfall": "Estimated average monthly shortfall: {v} kWh",
        "energy_balanced": "Estimated solar generation approximately matches household consumption.",

        "report_header": "Feasibility Report",
        "pdf_btn": "📄 Download Report (PDF)",
        "pdf_err": "Could not generate the PDF report: {error}",

        "assumptions_expander": "View assumptions and limitations",
        "assumptions_used": "Assumptions used",
        "col_assumption": "Assumption",
        "col_value": "Value",
        "col_source": "Source",
        "src_override": "your override",
        "src_file": "data/assumptions.json",
        "source_line": "{label}: as of {as_of}, {status}{link}",
        "status_verified": "verified",
        "status_unverified": "unverified",
        "status_estimate": "market estimate",
        "source_word": "source",
        "limitations_header": "Limitations",
        "slab_upto": "up to {n} kWh: ৳{rate}",
        "slab_above": "above that: ৳{rate}",

        # ----- chat -----
        "chat_header": "Ask Bangla Solar AI",
        "chat_placeholder": "Ask about solar panels, generation, costs, savings or batteries...",
        "agent_no_text": "The agent finished without returning a text response. Check the execution trace.",
        "trace_title": "🔧 Agent Execution Trace ({n} tool calls)",
        "trace_nodes": "**Graph nodes executed:**",
        "trace_none": "The agent did not request any tools for this message.",
        "trace_args": "Arguments sent to the tool",
        "trace_result": "Tool result",
        "trace_other": "Other tool results",
        "trace_tool": "Tool: `{name}`",
        "agent_fail": "Agent request failed: {error}",

        # ----- assumption names -----
        "a.tariff.lifeline_limit_kwh": "Lifeline limit (kWh)",
        "a.tariff.lifeline_rate_bdt": "Lifeline rate (৳/kWh)",
        "a.tariff.slabs": "Tariff slabs",
        "a.tariff.vat_rate": "VAT rate",
        "a.tariff.demand_charge_per_kw_bdt": "Demand charge (৳ per kW per month)",
        "a.tariff.sanctioned_load_kw": "Sanctioned load (kW)",
        "a.net_metering.enabled_by_default": "Net metering on by default",
        "a.net_metering.settlement_months": "Settlement months",
        "a.net_metering.standard_surplus_rate_bdt_per_kwh": "Standard surplus rate (৳/kWh)",
        "a.net_metering.incentive_rate_bdt_per_kwh": "Incentive surplus rate (৳/kWh)",
        "a.net_metering.incentive_requires_battery": "Incentive needs a battery",
        "a.net_metering.incentive_install_deadline": "Incentive install deadline",
        "a.net_metering.incentive_valid_until": "Incentive paid until",
        "a.net_metering.max_capacity_fraction_of_sanctioned_load": "Max system size (share of sanctioned load)",
        "a.costs.solar_cost_per_kw_bdt": "Solar cost (৳ per kW)",
        "a.costs.battery_cost_per_kwh_bdt": "Battery cost (৳ per kWh)",
        "a.roof.usable_fraction": "Usable share of roof",
        "a.roof.area_per_kw_sqm": "Roof area per kW (m²)",
        "a.battery.depth_of_discharge": "Battery depth of discharge",
        "a.battery.inverter_efficiency": "Inverter efficiency",
        "a.pvgis.api_url": "PVGIS API address",
        "a.pvgis.timeout_seconds": "PVGIS timeout (seconds)",
        "a.pvgis.system_loss_percent": "System losses (%)",
        "a.pvgis.angle_degrees": "Panel tilt (degrees)",
        "a.pvgis.aspect_degrees": "Panel direction (degrees)",
        "a.pvgis.use_optimal_angles": "Use PVGIS optimal angles",
        "a.sizing.target_offset_fraction": "Share of consumption to cover",
        "a.profile.monthly_consumption_factors": "Seasonal use factors (Jan-Dec)",

        # ----- report / PDF -----
        "pdf_brand": "Bangla Solar AI",
        "pdf_footer": "Bangla Solar AI - Preliminary estimates | Page {n}",
        "pdf_title": "Bangla Solar AI - Solar Feasibility Report",
        "pdf_summary": "Your Solar Assessment",
        "pdf_energy": "Energy Assessment",
        "pdf_details": "Assessment Details",
        "pdf_report": "Feasibility Report",
        "pdf_monthly": "Month by Month",
        "pdf_capacity": "Solar Capacity",
        "pdf_generation": "Monthly Generation",
        "pdf_cost": "Estimated Cost",
        "pdf_consumption": "Monthly Consumption",
        "pdf_savings": "Average Monthly Savings",
        "pdf_annual_savings": "Annual Savings",
        "pdf_surplus_paid": "Surplus Payments (per year)",
        "pdf_payback": "Simple Payback",
        "pdf_est_gen": "Estimated Monthly Solar Generation",
        "pdf_est_cons": "Estimated Monthly Consumption",
        "pdf_surplus": "Estimated Average Monthly Surplus",
        "pdf_shortfall": "Estimated Average Monthly Shortfall",
        "pdf_balance": "Generation vs Consumption",
        "pdf_balanced": "Approximately balanced",
        "pdf_location": "Location",
        "pdf_bill": "Monthly Electricity Bill",
        "pdf_roof": "Roof Area",
        "pdf_load": "Sanctioned Load",
        "pdf_battery": "Battery Backup",
        "pdf_required": "Required",
        "pdf_not_required": "Not required",
        "pdf_backup_load": "Backup Load",
        "pdf_backup_hours": "Backup Duration",
        "pdf_hours": "{n} hours",
        "pdf_net_metering": "Net Metering",
        "pdf_on": "On",
        "pdf_off": "Off",
        "pdf_col_month": "Month",
        "pdf_col_use": "Use kWh",
        "pdf_col_solar": "Solar kWh",
        "pdf_col_before": "Bill before",
        "pdf_col_after": "Bill after",
        "pdf_col_paid": "Surplus paid",
    },

    "bn": {
        # ----- general -----
        "language_label": "Language / ভাষা",
        "app_title": "☀️ বাংলা সোলার AI",
        "app_caption": "বাংলায় আপনার ছাদের সৌরবিদ্যুৎ সম্ভাব্যতা যাচাই করুন",
        "na": "প্রযোজ্য নয়",
        "yes": "হ্যাঁ",
        "no": "না",
        "years": "{n} বছর",
        "kwh": "{n} কিলোওয়াট-ঘণ্টা",
        "kw": "{n} কিলোওয়াট",

        # ----- sidebar -----
        "sidebar_header": "সোলার মূল্যায়ন",
        "location": "অবস্থান",
        "location_ph": "যেমন: বরিশাল, বাংলাদেশ",
        "monthly_bill": "মাসিক বিদ্যুৎ বিল (টাকা)",
        "roof_area": "ছাদের আয়তন (বর্গমিটার)",
        "sanctioned_load": "মঞ্জুরকৃত লোড (কিলোওয়াট)",
        "sanctioned_load_help": "আপনার বিদ্যুৎ বিলে ছাপা থাকে। এটি আপনার নির্দিষ্ট ডিমান্ড চার্জ এবং নেট মিটারিংয়ে সর্বোচ্চ কত বড় সিস্টেম বসানো যাবে তা ঠিক করে।",
        "needs_battery": "আমার ব্যাটারি ব্যাকআপ দরকার",
        "backup_load": "ব্যাকআপ লোড (কিলোওয়াট)",
        "backup_hours": "ব্যাকআপের সময় (ঘণ্টা)",
        "net_metering": "আমি নেট মিটারিং ব্যবহার করব",
        "net_metering_help": "নেট মিটারিং গাইডলাইন ২০২৫ অনুযায়ী উদ্বৃত্ত বিদ্যুৎ ক্রেডিট ও মূল্য পাবে।",
        "advanced": "উন্নত: নিজের দাম ব্যবহার করুন",
        "advanced_caption": "ডিফল্ট মান data/assumptions.json থেকে আসে। আপনার ইনস্টলারের কোটেশন বা বিলের সংখ্যা ব্যবহার করতে মান বদলান।",
        "solar_cost": "সোলারের খরচ (প্রতি কিলোওয়াট, টাকা)",
        "battery_cost": "ব্যাটারির খরচ (প্রতি কিলোওয়াট-ঘণ্টা, টাকা)",
        "vat_percent": "বিলের ভ্যাট (%)",
        "surplus_rate": "উদ্বৃত্ত বিদ্যুতের মূল্য (প্রতি ইউনিট, টাকা)",
        "area_per_kw": "প্রতি কিলোওয়াট প্যানেলের জন্য ছাদের জায়গা (বর্গমিটার)",
        "assess_btn": "সোলার সম্ভাবনা যাচাই করুন",
        "clear_btn": "কথোপকথন মুছুন",

        # ----- messages -----
        "warn_enter_location": "অনুগ্রহ করে আপনার অবস্থান লিখুন।",
        "warn_bill_positive": "অনুগ্রহ করে শূন্যের চেয়ে বেশি মাসিক বিল দিন।",
        "spinner_calc": "সোলার সম্ভাবনা হিসাব করা হচ্ছে...",
        "err_assumptions_file": "অনুমানের ফাইলে সমস্যা: {error}",
        "err_location_not_found": "অবস্থান খুঁজে পাওয়া যায়নি: {location}",

        # ----- results -----
        "assess_header": "আপনার সোলার মূল্যায়ন",
        "m_capacity": "সোলার ক্ষমতা",
        "m_monthly_gen": "মাসিক উৎপাদন",
        "m_cost": "আনুমানিক খরচ",
        "check_title": "সংখ্যাগুলোর ওপর নির্ভর করার আগে এই অনুমানগুলো যাচাই করুন:",
        "check_hint": "সাইডবারে “উন্নত: নিজের দাম ব্যবহার করুন” অংশে আপনার নিজের মান দিতে পারেন।",
        "warn_unverified": "যাচাই করা হয়নি: {label}। {note}",
        "warn_estimate": "বাজারের আনুমানিক মান: {label}। {note}",
        "warn_stale": "পুরোনো তথ্য: {label} {age} দিন আগের ({as_of} তারিখের)। অনুগ্রহ করে সূত্র যাচাই করুন।",
        "warn_bad_date": "{label}-এর তারিখ পড়া যাচ্ছে না। YYYY-MM-DD ফরম্যাট ব্যবহার করুন।",

        "savings_header": "সঞ্চয় ও পে-ব্যাক",
        "m_monthly_savings": "গড় মাসিক সঞ্চয়",
        "m_bill_after": "সোলারের পর গড় বিল",
        "m_payback": "সহজ পে-ব্যাক",
        "info_roof_limited": "আপনার ছাদে {roof} কিলোওয়াট বসানো যায়, যা আপনার গড় ব্যবহার পূরণে প্রয়োজনীয় {demand} কিলোওয়াটের চেয়ে কম। তাই সিস্টেমের আকার ছাদ অনুযায়ী ঠিক করা হয়েছে।",
        "info_consumption_sized": "সিস্টেমটি আপনার গড় ব্যবহার পূরণের জন্য ({demand} কিলোওয়াট) ঠিক করা হয়েছে। আপনার ছাদে {roof} কিলোওয়াট পর্যন্ত বসানো যেত।",
        "battery_payback": "ব্যাকআপ ব্যাটারিসহ পে-ব্যাক: {n} বছর। ব্যাকআপ ব্যাটারি আপনার বিল কমায় না।",
        "nm_on_standard": "নেট মিটারিং চালু। উদ্বৃত্ত বিদ্যুতের মূল্য প্রতি ইউনিট প্রায় ৳{rate} ধরা হয়েছে (আনুমানিক বাল্ক রেট)।",
        "nm_on_incentive": "নেট মিটারিং চালু, এবং আপনার ব্যাটারিসহ সিস্টেম প্রতি ইউনিট ৳{rate} উদ্বৃত্ত প্রণোদনার যোগ্য ({deadline}-এর মধ্যে স্থাপন করলে, {until} পর্যন্ত প্রদেয়)।",
        "nm_off": "নেট মিটারিং বন্ধ: উদ্বৃত্ত বিদ্যুতের কোনো মূল্য ধরা হয়নি।",
        "nm_load_warning": "এই {capacity} কিলোওয়াটের সিস্টেম আপনার {load} কিলোওয়াট মঞ্জুরকৃত লোডে নেট মিটারিংয়ের অনুমোদিত {allowed} কিলোওয়াটের চেয়ে বড়। লোড বাড়ানোর আবেদন করতে হতে পারে।",

        "monthly_header": "মাসের পর মাস",
        "monthly_caption": "উৎপাদন PVGIS-এর সাধারণ আবহাওয়ার ধরন অনুসরণ করে। রোদেলা মাসের ক্রেডিট পরের মাসে জমা থাকে এবং নির্ধারিত মাসে নিষ্পত্তি হয়।",
        "chart_energy": "সোলার উৎপাদন বনাম আপনার ব্যবহার (কিলোওয়াট-ঘণ্টা)",
        "chart_bills": "সোলারের আগে ও পরে বিল (টাকা)",
        "series_generation": "সোলার উৎপাদন",
        "series_consumption": "আপনার ব্যবহার",
        "series_before": "সোলারের আগে বিল",
        "series_after": "সোলারের পরে বিল",
        "col_month": "মাস",
        "col_consumption": "ব্যবহার (কি.ও.ঘ.)",
        "col_generation": "সোলার (কি.ও.ঘ.)",
        "col_billed": "বিলযোগ্য ইউনিট",
        "col_credit": "ক্রেডিট (কি.ও.ঘ.)",
        "col_before": "আগের বিল (৳)",
        "col_after": "পরের বিল (৳)",
        "col_payout": "উদ্বৃত্ত বাবদ প্রাপ্তি (৳)",
        "col_savings": "সঞ্চয় (৳)",

        "energy_header": "বিদ্যুৎ মূল্যায়ন",
        "m_est_gen": "আনুমানিক মাসিক সোলার উৎপাদন",
        "m_est_cons": "আনুমানিক মাসিক ব্যবহার",
        "energy_surplus": "আনুমানিক গড় মাসিক উদ্বৃত্ত: {v} কিলোওয়াট-ঘণ্টা",
        "energy_shortfall": "আনুমানিক গড় মাসিক ঘাটতি: {v} কিলোওয়াট-ঘণ্টা",
        "energy_balanced": "আনুমানিক সোলার উৎপাদন পরিবারের ব্যবহারের প্রায় সমান।",

        "report_header": "সম্ভাব্যতা প্রতিবেদন",
        "pdf_btn": "📄 প্রতিবেদন ডাউনলোড করুন (PDF)",
        "pdf_err": "PDF প্রতিবেদন তৈরি করা যায়নি: {error}",

        "assumptions_expander": "অনুমান ও সীমাবদ্ধতা দেখুন",
        "assumptions_used": "ব্যবহৃত অনুমান",
        "col_assumption": "অনুমান",
        "col_value": "মান",
        "col_source": "উৎস",
        "src_override": "আপনার দেওয়া মান",
        "src_file": "data/assumptions.json",
        "source_line": "{label}: {as_of} পর্যন্ত, {status}{link}",
        "status_verified": "যাচাইকৃত",
        "status_unverified": "যাচাই করা হয়নি",
        "status_estimate": "বাজারের আনুমানিক মান",
        "source_word": "উৎস",
        "limitations_header": "সীমাবদ্ধতা",
        "slab_upto": "{n} ইউনিট পর্যন্ত: ৳{rate}",
        "slab_above": "তার ওপরে: ৳{rate}",

        # ----- chat -----
        "chat_header": "বাংলা সোলার AI-কে জিজ্ঞাসা করুন",
        "chat_placeholder": "সোলার প্যানেল, উৎপাদন, খরচ, সঞ্চয় বা ব্যাটারি নিয়ে জিজ্ঞাসা করুন...",
        "agent_no_text": "এজেন্ট কোনো লিখিত উত্তর না দিয়েই শেষ করেছে। এক্সিকিউশন ট্রেস দেখুন।",
        "trace_title": "🔧 এজেন্ট এক্সিকিউশন ট্রেস ({n}টি টুল কল)",
        "trace_nodes": "**চালু হওয়া গ্রাফ নোড:**",
        "trace_none": "এই বার্তার জন্য এজেন্ট কোনো টুল ব্যবহার করেনি।",
        "trace_args": "টুলে পাঠানো আর্গুমেন্ট",
        "trace_result": "টুলের ফলাফল",
        "trace_other": "অন্যান্য টুলের ফলাফল",
        "trace_tool": "টুল: `{name}`",
        "agent_fail": "এজেন্টের অনুরোধ ব্যর্থ হয়েছে: {error}",

        # ----- assumption names -----
        "a.tariff.lifeline_limit_kwh": "লাইফলাইন সীমা (কি.ও.ঘ.)",
        "a.tariff.lifeline_rate_bdt": "লাইফলাইন রেট (৳/কি.ও.ঘ.)",
        "a.tariff.slabs": "ট্যারিফ স্ল্যাব",
        "a.tariff.vat_rate": "ভ্যাটের হার",
        "a.tariff.demand_charge_per_kw_bdt": "ডিমান্ড চার্জ (৳ প্রতি কিলোওয়াট প্রতি মাস)",
        "a.tariff.sanctioned_load_kw": "মঞ্জুরকৃত লোড (কিলোওয়াট)",
        "a.net_metering.enabled_by_default": "নেট মিটারিং ডিফল্টে চালু",
        "a.net_metering.settlement_months": "নিষ্পত্তির মাস",
        "a.net_metering.standard_surplus_rate_bdt_per_kwh": "সাধারণ উদ্বৃত্ত মূল্য (৳/কি.ও.ঘ.)",
        "a.net_metering.incentive_rate_bdt_per_kwh": "প্রণোদনার উদ্বৃত্ত মূল্য (৳/কি.ও.ঘ.)",
        "a.net_metering.incentive_requires_battery": "প্রণোদনার জন্য ব্যাটারি দরকার",
        "a.net_metering.incentive_install_deadline": "প্রণোদনার জন্য স্থাপনের শেষ তারিখ",
        "a.net_metering.incentive_valid_until": "প্রণোদনা প্রদেয় পর্যন্ত",
        "a.net_metering.max_capacity_fraction_of_sanctioned_load": "সর্বোচ্চ সিস্টেম (মঞ্জুরকৃত লোডের অনুপাত)",
        "a.costs.solar_cost_per_kw_bdt": "সোলারের খরচ (৳ প্রতি কিলোওয়াট)",
        "a.costs.battery_cost_per_kwh_bdt": "ব্যাটারির খরচ (৳ প্রতি কিলোওয়াট-ঘণ্টা)",
        "a.roof.usable_fraction": "ছাদের ব্যবহারযোগ্য অংশ",
        "a.roof.area_per_kw_sqm": "প্রতি কিলোওয়াটে ছাদের জায়গা (বর্গমিটার)",
        "a.battery.depth_of_discharge": "ব্যাটারির ডিসচার্জ গভীরতা",
        "a.battery.inverter_efficiency": "ইনভার্টারের দক্ষতা",
        "a.pvgis.api_url": "PVGIS API ঠিকানা",
        "a.pvgis.timeout_seconds": "PVGIS টাইমআউট (সেকেন্ড)",
        "a.pvgis.system_loss_percent": "সিস্টেমের ক্ষতি (%)",
        "a.pvgis.angle_degrees": "প্যানেলের ঢাল (ডিগ্রি)",
        "a.pvgis.aspect_degrees": "প্যানেলের দিক (ডিগ্রি)",
        "a.pvgis.use_optimal_angles": "PVGIS-এর সর্বোত্তম কোণ ব্যবহার",
        "a.sizing.target_offset_fraction": "ব্যবহারের যে অংশ পূরণ করা হবে",
        "a.profile.monthly_consumption_factors": "মৌসুমি ব্যবহারের গুণক (জানুয়ারি–ডিসেম্বর)",

        # ----- report / PDF -----
        "pdf_brand": "বাংলা সোলার AI",
        "pdf_footer": "বাংলা সোলার AI - প্রাথমিক অনুমান | পৃষ্ঠা {n}",
        "pdf_title": "বাংলা সোলার AI - সৌরবিদ্যুৎ সম্ভাব্যতা প্রতিবেদন",
        "pdf_summary": "আপনার সোলার মূল্যায়ন",
        "pdf_energy": "বিদ্যুৎ মূল্যায়ন",
        "pdf_details": "মূল্যায়নের বিবরণ",
        "pdf_report": "সম্ভাব্যতা প্রতিবেদন",
        "pdf_monthly": "মাসের পর মাস",
        "pdf_capacity": "সোলার ক্ষমতা",
        "pdf_generation": "মাসিক উৎপাদন",
        "pdf_cost": "আনুমানিক খরচ",
        "pdf_consumption": "মাসিক ব্যবহার",
        "pdf_savings": "গড় মাসিক সঞ্চয়",
        "pdf_annual_savings": "বার্ষিক সঞ্চয়",
        "pdf_surplus_paid": "উদ্বৃত্ত বাবদ প্রাপ্তি (বছরে)",
        "pdf_payback": "সহজ পে-ব্যাক",
        "pdf_est_gen": "আনুমানিক মাসিক সোলার উৎপাদন",
        "pdf_est_cons": "আনুমানিক মাসিক ব্যবহার",
        "pdf_surplus": "আনুমানিক গড় মাসিক উদ্বৃত্ত",
        "pdf_shortfall": "আনুমানিক গড় মাসিক ঘাটতি",
        "pdf_balance": "উৎপাদন বনাম ব্যবহার",
        "pdf_balanced": "প্রায় সমান",
        "pdf_location": "অবস্থান",
        "pdf_bill": "মাসিক বিদ্যুৎ বিল",
        "pdf_roof": "ছাদের আয়তন",
        "pdf_load": "মঞ্জুরকৃত লোড",
        "pdf_battery": "ব্যাটারি ব্যাকআপ",
        "pdf_required": "প্রয়োজন",
        "pdf_not_required": "প্রয়োজন নেই",
        "pdf_backup_load": "ব্যাকআপ লোড",
        "pdf_backup_hours": "ব্যাকআপের সময়",
        "pdf_hours": "{n} ঘণ্টা",
        "pdf_net_metering": "নেট মিটারিং",
        "pdf_on": "চালু",
        "pdf_off": "বন্ধ",
        "pdf_col_month": "মাস",
        "pdf_col_use": "ব্যবহার",
        "pdf_col_solar": "সোলার",
        "pdf_col_before": "আগের বিল",
        "pdf_col_after": "পরের বিল",
        "pdf_col_paid": "উদ্বৃত্ত প্রাপ্তি",
    },
}


def t(lang: str, key: str, **values) -> str:
    """Look up UI text. Falls back to English, then to the key itself."""

    table = TEXT.get(lang) or TEXT[DEFAULT_LANGUAGE]
    text = table.get(key)

    if text is None:
        text = TEXT[DEFAULT_LANGUAGE].get(key, key)

    if values:
        text = text.format(**{
            k: digits(lang, v) if isinstance(v, (int, float)) else v
            for k, v in values.items()
        })

    return text


# ----------------------------------------------------------
# Limitation sentences (the engine writes them in English)
# ----------------------------------------------------------

LIMITATION_BN = {
    "Solar generation is estimated using PVGIS data for the resolved coordinates.":
        "সৌর বিদ্যুৎ উৎপাদন নির্ধারিত স্থানাঙ্কের PVGIS তথ্য থেকে অনুমান করা হয়েছে।",
    "Roof shading, orientation, tilt, and structural suitability have not been inspected.":
        "ছাদের ছায়া, দিক, ঢাল ও কাঠামোগত উপযুক্ততা পরীক্ষা করা হয়নি।",
    "Electricity consumption is estimated from your bill using the BERC residential slab tariff, the demand charge for your sanctioned load and VAT; meter rent and rebates are not included.":
        "বিদ্যুৎ ব্যবহার আপনার বিল থেকে BERC আবাসিক স্ল্যাব ট্যারিফ, মঞ্জুরকৃত লোডের ডিমান্ড চার্জ ও ভ্যাট ধরে অনুমান করা হয়েছে; মিটার ভাড়া ও রিবেট ধরা হয়নি।",
    "Equipment costs are market estimates, not verified current quotations.":
        "যন্ত্রপাতির খরচ বাজারের আনুমানিক মূল্য; যাচাইকৃত বর্তমান কোটেশন নয়।",
    "Actual output depends on installation and weather conditions.":
        "প্রকৃত উৎপাদন স্থাপনার ধরন ও আবহাওয়ার ওপর নির্ভর করবে।",
    "Roof capacity is estimated from an assumed panel area per kW and usable roof fraction (see the assumptions used).":
        "ছাদের ধারণক্ষমতা প্রতি কিলোওয়াটে ধরা প্যানেলের জায়গা ও ছাদের ব্যবহারযোগ্য অংশের অনুমানের ভিত্তিতে হিসাব করা হয়েছে।",
    "Payback ignores tariff changes, panel degradation, maintenance, financing, and battery replacement.":
        "পে-ব্যাক হিসাবে ট্যারিফ পরিবর্তন, প্যানেলের ক্ষয়, রক্ষণাবেক্ষণ, ঋণের সুদ ও ব্যাটারি প্রতিস্থাপন ধরা হয়নি।",
    "Every month is assumed to use the same amount of electricity unless a seasonal pattern is set in the assumptions.":
        "অনুমানে মৌসুমি ধরন না দিলে প্রতি মাসে সমান বিদ্যুৎ ব্যবহার ধরা হয়েছে।",
    "Monthly generation follows the PVGIS typical-weather profile; real months will vary.":
        "মাসভিত্তিক উৎপাদন PVGIS-এর সাধারণ আবহাওয়ার ধরন অনুসরণ করে; আসল মাসে ভিন্ন হতে পারে।",
    "Annual generation divided by 12 is an average, not a month-specific forecast.":
        "বার্ষিক উৎপাদনকে ১২ দিয়ে ভাগ করা একটি গড়, নির্দিষ্ট মাসের পূর্বাভাস নয়।",
    "Net metering is modelled as monthly netting with credit carried forward and settled in the settlement months; actual rules and rates may differ by distribution company.":
        "নেট মিটারিং মাসভিত্তিক সমন্বয় হিসেবে ধরা হয়েছে; ক্রেডিট পরের মাসে জমা থাকে এবং নির্ধারিত মাসে নিষ্পত্তি হয়। বিতরণ কোম্পানিভেদে আসল নিয়ম ও হার ভিন্ন হতে পারে।",
    "Surplus is paid at an estimated bulk rate; confirm the rate with your distribution company.":
        "উদ্বৃত্ত বিদ্যুতের মূল্য আনুমানিক বাল্ক রেটে ধরা হয়েছে; হারটি আপনার বিতরণ কোম্পানির কাছ থেকে নিশ্চিত করুন।",
    "The surplus incentive rate applies only to eligible battery-backed systems installed before the scheme deadline, and is not guaranteed.":
        "উদ্বৃত্ত বিদ্যুতের প্রণোদনা হার শুধু যোগ্য ব্যাটারিসহ সিস্টেমে, প্রকল্পের শেষ তারিখের আগে স্থাপন করলে প্রযোজ্য; এটি নিশ্চিত নয়।",
    "The system is larger than your sanctioned load allows under net metering; you may need to apply for a load increase.":
        "নেট মিটারিংয়ে আপনার মঞ্জুরকৃত লোডের চেয়ে সিস্টেম বড়; লোড বাড়ানোর আবেদন করতে হতে পারে।",
    "Without net metering, surplus power is assumed to have no value.":
        "নেট মিটারিং ছাড়া উদ্বৃত্ত বিদ্যুতের কোনো মূল্য ধরা হয়নি।",
    "Some assumptions are unverified or may be out of date; verify prices and tariffs before deciding.":
        "কিছু অনুমান যাচাই করা হয়নি বা পুরোনো হতে পারে; সিদ্ধান্তের আগে দাম ও ট্যারিফ যাচাই করুন।",
    "The system size is limited by available roof area, so it will not cover all household consumption.":
        "ছাদের জায়গা সীমিত হওয়ায় সিস্টেমের আকার সীমিত; এটি পরিবারের পুরো বিদ্যুৎ ব্যবহার পূরণ করবে না।",
    "The system is sized to cover average household consumption; the roof could hold a larger system.":
        "সিস্টেমটি পরিবারের গড় বিদ্যুৎ ব্যবহার পূরণের জন্য নির্ধারিত; ছাদে আরও বড় সিস্টেম বসানো সম্ভব।",
}


def translate_limitation(lang: str, text: str) -> str:
    """Translate an engine limitation sentence; unknown text stays as is."""

    if lang == "bn":
        return LIMITATION_BN.get(text, text)

    return text
