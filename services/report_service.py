
import io
import re
from pathlib import Path

from functools import lru_cache

from fpdf import FPDF

from services.i18n import LIMITATION_BN, digits, fmt, month_name, t


# ==========================================================
# FONT CONFIGURATION
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = PROJECT_ROOT / "assets" / "fonts"

REGULAR_FONT = FONT_DIR / "NotoSansBengali-Regular.ttf"
BOLD_FONT = FONT_DIR / "NotoSansBengali-Bold.ttf"

# Optional Latin fonts. Some Noto Sans Bengali builds contain Bengali
# glyphs only (no English letters, ASCII digits or punctuation). When the
# files below exist they are used for every glyph the Bengali font lacks.
LATIN_REGULAR_FONT = FONT_DIR / "NotoSans-Regular.ttf"
LATIN_BOLD_FONT = FONT_DIR / "NotoSans-Bold.ttf"

# Characters the PDF needs from a Latin-capable font.
_LATIN_PROBE = "Aa0.,-:|()"


def _latin_fonts_available() -> bool:
    return LATIN_REGULAR_FONT.is_file() and LATIN_BOLD_FONT.is_file()


@lru_cache(maxsize=4)
def _font_covers_latin(path: str) -> bool:
    """True if the font has English letters, digits and punctuation."""

    from fontTools.ttLib import TTFont

    cmap = TTFont(path).getBestCmap()
    return all(ord(ch) in cmap for ch in _LATIN_PROBE)


def _validate_fonts():
    """Ensure both Unicode font files are available."""

    missing = [
        str(font)
        for font in (REGULAR_FONT, BOLD_FONT)
        if not font.is_file()
    ]

    if missing:
        raise FileNotFoundError(
            "Required PDF font files were not found:\n"
            + "\n".join(missing)
            + "\nDownload Noto Sans Bengali Regular and Bold "
              "and place them in assets/fonts/."
        )

    # Without Latin glyphs, English text, numbers and punctuation would
    # silently disappear from the PDF, so stop with a clear message.
    if not _latin_fonts_available() and not _font_covers_latin(
        str(REGULAR_FONT)
    ):
        raise RuntimeError(
            "The PDF font has no Latin glyphs, so English text, digits "
            "and punctuation would be missing. Add NotoSans-Regular.ttf "
            "and NotoSans-Bold.ttf to assets/fonts/, or use a Noto Sans "
            "Bengali build that includes Latin."
        )


# ==========================================================
# SOLAR FEASIBILITY REPORT
# ==========================================================

def generate_solar_report(
    result: dict,
    language: str = "en",
) -> str:
    """Generate a solar feasibility report in English or Bangla."""

    if language == "bn":
        title = "বাংলা সোলার AI — সৌরবিদ্যুৎ সম্ভাব্যতা প্রতিবেদন"
        location_label = "অবস্থান"
        roof_label = "মোট ছাদের আয়তন"
        usable_roof_label = "ব্যবহারযোগ্য ছাদের আয়তন"
        capacity_label = "প্রস্তাবিত সোলার ক্যাপাসিটি"
        generation_label = "আনুমানিক মাসিক বিদ্যুৎ উৎপাদন"
        consumption_label = "আনুমানিক মাসিক বিদ্যুৎ ব্যবহার"
        cost_label = "আনুমানিক মোট খরচ"
        battery_label = "আনুমানিক ব্যাটারি ক্যাপাসিটি"
        limitations_label = "সীমাবদ্ধতা"
        yearly_generation_label = "আনুমানিক বার্ষিক বিদ্যুৎ উৎপাদন"
        daily_generation_label = "আনুমানিক দৈনিক বিদ্যুৎ উৎপাদন"
        savings_label = "আনুমানিক মাসিক সঞ্চয়"
        payback_label = "আনুমানিক পে-ব্যাক সময়"
        years_unit = "বছর"
        annual_savings_label = "আনুমানিক বার্ষিক সঞ্চয়"
        surplus_paid_label = "উদ্বৃত্ত বিদ্যুৎ বাবদ বার্ষিক প্রাপ্তি"
        net_metering_label = "নেট মিটারিং"
        on_text, off_text = "চালু", "বন্ধ"
        rate_text = "উদ্বৃত্তের হার প্রতি ইউনিট ৳{rate}"

        disclaimer = (
            "এটি একটি প্রাথমিক অনুমান। ইনস্টলেশনের আগে "
            "যোগ্য সোলার পেশাজীবীর মাধ্যমে যাচাই করুন।"
        )

        limitation_translations = LIMITATION_BN

    else:
        title = "Bangla Solar AI — Solar Feasibility Report"
        location_label = "Location"
        roof_label = "Total roof area"
        usable_roof_label = "Usable roof area"
        capacity_label = "Estimated solar capacity"
        generation_label = "Estimated monthly generation"
        consumption_label = "Estimated monthly consumption"
        cost_label = "Estimated total cost"
        battery_label = "Estimated battery capacity"
        limitations_label = "Limitations"
        yearly_generation_label = "Estimated yearly generation"
        daily_generation_label = "Estimated daily generation"
        savings_label = "Estimated monthly savings"
        payback_label = "Estimated payback period"
        years_unit = "years"
        annual_savings_label = "Estimated annual savings"
        surplus_paid_label = "Yearly payment for surplus power"
        net_metering_label = "Net metering"
        on_text, off_text = "On", "Off"
        rate_text = "surplus paid at ৳{rate} per unit"

        disclaimer = (
            "This is a preliminary estimate. Consult a qualified "
            "solar professional before installation."
        )

        limitation_translations = {}

    electricity = result["electricity"]
    generation = result["generation"]
    cost = result["cost"]
    battery = result.get("battery")

    lines = [
        f"# {title}",
        "",
        f"- **{location_label}:** {result['location']}",
        f"- **{roof_label}:** {result['roof_area_sqm']} m²",
        f"- **{usable_roof_label}:** "
        f"{result['usable_roof_area_sqm']} m²",
        f"- **{capacity_label}:** {result['solar_capacity_kw']} kW",
        f"- **{daily_generation_label}:** "
        f"{generation['daily_generation_kwh']} kWh",
        f"- **{generation_label}:** "
        f"{generation['monthly_generation_kwh']} kWh",
    ]

    if "yearly_generation_kwh" in generation:
        lines.append(
            f"- **{yearly_generation_label}:** "
            f"{generation['yearly_generation_kwh']} kWh"
        )

    lines.extend([
        f"- **{consumption_label}:** "
        f"{electricity['monthly_consumption_kwh']} kWh",
        f"- **{cost_label}:** "
        f"৳{cost['total_cost_bdt']:,.2f}",
    ])

    savings = result.get("savings")

    if savings:
        lines.append(
            f"- **{savings_label}:** "
            f"৳{savings['monthly_savings_bdt']:,.0f}"
        )

        if savings.get("annual_savings_bdt") is not None:
            lines.append(
                f"- **{annual_savings_label}:** "
                f"৳{savings['annual_savings_bdt']:,.0f}"
            )

        if savings.get("annual_payout_bdt"):
            lines.append(
                f"- **{surplus_paid_label}:** "
                f"৳{savings['annual_payout_bdt']:,.0f}"
            )

        if savings.get("payback_years") is not None:
            lines.append(
                f"- **{payback_label}:** "
                f"{savings['payback_years']:.1f} {years_unit}"
            )

    net_info = result.get("net_metering_info")

    if net_info:
        status = on_text if net_info["enabled"] else off_text

        if net_info["enabled"] and net_info.get("surplus_rate_bdt_per_kwh"):
            status += (
                " — "
                + rate_text.format(
                    rate=f"{net_info['surplus_rate_bdt_per_kwh']:g}"
                )
            )

        lines.append(f"- **{net_metering_label}:** {status}")

    if battery:
        lines.append(
            f"- **{battery_label}:** "
            f"{battery['battery_capacity_kwh']} kWh"
        )

    lines.extend(["", f"## {limitations_label}"])

    for limitation in result.get("limitations", []):
        lines.append(
            f"- {limitation_translations.get(limitation, limitation)}"
        )

    note_label = "দ্রষ্টব্য" if language == "bn" else "Note"
    lines.extend(["", f"**{note_label}:** {disclaimer}"])

    return digits(language, "\n".join(lines))


# ==========================================================
# PDF DOCUMENT
# ==========================================================

class SolarReportPDF(FPDF):
    """A4 report with Unicode fonts and Bangla text shaping."""

    language = "en"

    def header(self):
        self.set_font("Noto", style="B", size=9)
        self.cell(
            0,
            7,
            t(self.language, "pdf_brand"),
            new_x="LMARGIN",
            new_y="NEXT",
        )

        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.2)

        self.line(
            self.l_margin,
            self.get_y(),
            self.w - self.r_margin,
            self.get_y(),
        )
        self.ln(4)

    def footer(self):
        self.set_y(-12)
        self.set_font("Noto", size=8)

        self.cell(
            0,
            6,
            t(self.language, "pdf_footer", n=self.page_no()),
            align="C",
        )

    def section_title(self, title, size=12):
        self.ln(3)
        self.set_font("Noto", style="B", size=size)
        self.multi_cell(0, 8, str(title))
        self.ln(1)

    def body_text(self, text):
        self.set_font("Noto", size=9)
        self.multi_cell(0, 6, str(text))
        self.ln(1)

    def key_value(self, label, value):
        """Render a label and value as readable report text."""

        self.set_font("Noto", style="B", size=9)
        self.write(6, f"{label}: ")

        self.set_font("Noto", size=9)
        self.multi_cell(0, 6, str(value))

    def bordered_key_value(self, label, value):
        """Render a simple bordered row without color fills."""

        left_width = 55
        right_width = (
            self.w - self.l_margin - self.r_margin - left_width
        )

        label_text = str(label)
        value_text = str(value)

        self.set_font("Noto", style="B", size=9)
        label_lines = self.multi_cell(
            left_width - 4,
            5,
            label_text,
            dry_run=True,
            output="LINES",
        )

        self.set_font("Noto", size=9)
        value_lines = self.multi_cell(
            right_width - 4,
            5,
            value_text,
            dry_run=True,
            output="LINES",
        )

        row_height = max(
            len(label_lines),
            len(value_lines),
            1,
        ) * 5 + 4

        # Start a new page if the row would overflow.
        if self.get_y() + row_height > self.page_break_trigger:
            self.add_page()

        x = self.get_x()
        y = self.get_y()

        self.rect(
            x,
            y,
            left_width,
            row_height,
        )
        self.rect(
            x + left_width,
            y,
            right_width,
            row_height,
        )

        self.set_xy(x + 2, y + 2)
        self.set_font("Noto", style="B", size=9)
        self.multi_cell(
            left_width - 4,
            5,
            label_text,
        )

        self.set_xy(x + left_width + 2, y + 2)
        self.set_font("Noto", size=9)
        self.multi_cell(
            right_width - 4,
            5,
            value_text,
        )

        self.set_xy(x, y + row_height)


# ==========================================================
# FORMATTING HELPERS
# ==========================================================

def _format_number(value, decimals=2):
    """Format numeric values for display."""

    if value is None:
        return "Not available"

    try:
        return f"{float(value):,.{decimals}f}"
    except (TypeError, ValueError):
        return str(value)


def _clean_markdown(text):
    """Convert basic Markdown to readable plain text."""

    text = str(text).strip()

    # Remove inline bold and italic markers.
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"__(.*?)__", r"\1", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", text)
    text = re.sub(r"(?<!_)_([^_]+)_(?!_)", r"\1", text)

    # Remove inline code markers.
    text = re.sub(r"`([^`]+)`", r"\1", text)

    # Preserve readable link labels.
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    return text.strip()


# ==========================================================
# MARKDOWN TO PDF
# ==========================================================

def _markdown_to_pdf(pdf, report):
    """Render headings, lists, blockquotes, tables and paragraphs."""

    lines = report.splitlines()
    index = 0

    def is_table_row(line):
        return line.strip().startswith("|") and "|" in line.strip()[1:]

    def parse_table_row(line):
        return [
            cell.strip()
            for cell in line.strip().strip("|").split("|")
        ]

    while index < len(lines):
        line = lines[index].strip()

        if not line:
            index += 1
            continue

        # Ignore Markdown table separator rows.
        if re.fullmatch(r"\|?[\s|:-]+\|?", line):
            index += 1
            continue

        # Headings.
        heading = re.match(r"^(#{1,3})\s+(.+)$", line)

        if heading:
            level = len(heading.group(1))
            size = {1: 15, 2: 12, 3: 10}[level]

            pdf.section_title(
                _clean_markdown(heading.group(2)),
                size=size,
            )

            index += 1
            continue

        # Horizontal rules.
        if line in ("---", "***", "___"):
            y = pdf.get_y()
            pdf.line(
                pdf.l_margin,
                y,
                pdf.w - pdf.r_margin,
                y,
            )
            pdf.ln(3)

            index += 1
            continue

        # Markdown tables.
        if is_table_row(line):
            table_rows = []

            while (
                index < len(lines)
                and is_table_row(lines[index].strip())
            ):
                row = parse_table_row(lines[index])

                is_separator = all(
                    re.fullmatch(
                        r":?-{2,}:?",
                        cell.replace(" ", ""),
                    )
                    for cell in row
                )

                if not is_separator:
                    table_rows.append([
                        _clean_markdown(cell)
                        for cell in row
                    ])

                index += 1

            if table_rows:
                column_count = max(
                    len(row) for row in table_rows
                )

                for row in table_rows:
                    while len(row) < column_count:
                        row.append("")

                available_width = (
                    pdf.w - pdf.l_margin - pdf.r_margin
                )
                column_width = available_width / column_count

                for row_index, row in enumerate(table_rows):
                    if row_index == 0:
                        pdf.set_font("Noto", style="B", size=8)
                    else:
                        pdf.set_font("Noto", size=8)

                    # Text-based table rendering keeps all cells
                    # readable without risking clipped Bangla text.
                    pdf.body_text("  |  ".join(row))

                pdf.ln(2)

            continue

        # Unordered lists.
        bullet = re.match(r"^[-*+]\s+(.+)$", line)

        if bullet:
            pdf.body_text("• " + _clean_markdown(bullet.group(1)))
            index += 1
            continue

        # Ordered lists.
        numbered = re.match(r"^(\d+)[.)]\s+(.+)$", line)

        if numbered:
            pdf.body_text(
                f"{numbered.group(1)}. "
                f"{_clean_markdown(numbered.group(2))}"
            )
            index += 1
            continue

        # Blockquotes.
        if line.startswith(">"):
            pdf.body_text(_clean_markdown(line.lstrip("> ")))
            index += 1
            continue

        # Normal paragraph; join consecutive lines.
        paragraph_lines = [line]
        index += 1

        while index < len(lines):
            next_line = lines[index].strip()

            if (
                not next_line
                or re.match(r"^#{1,3}\s+", next_line)
                or is_table_row(next_line)
                or next_line.startswith(">")
                or re.match(r"^[-*+]\s+", next_line)
                or re.match(r"^\d+[.)]\s+", next_line)
                or next_line in ("---", "***", "___")
            ):
                break

            paragraph_lines.append(next_line)
            index += 1

        pdf.body_text(
            _clean_markdown(" ".join(paragraph_lines))
        )


# ==========================================================
# ASSESSMENT SUMMARY
# ==========================================================

def _monthly_table(pdf, rows, lang):
    """Compact 12-month table: use, solar, bill before/after, surplus paid."""

    headers = [
        t(lang, "pdf_col_month"),
        t(lang, "pdf_col_use"),
        t(lang, "pdf_col_solar"),
        t(lang, "pdf_col_before"),
        t(lang, "pdf_col_after"),
        t(lang, "pdf_col_paid"),
    ]

    usable = pdf.w - pdf.l_margin - pdf.r_margin
    widths = [usable * share for share in (0.20, 0.14, 0.14, 0.18, 0.18, 0.16)]
    height = 6

    def draw(cells, bold=False):
        if pdf.get_y() + height > pdf.page_break_trigger:
            pdf.add_page()

        pdf.set_font("Noto", style="B" if bold else "", size=8)

        for index, (width, text) in enumerate(zip(widths, cells)):
            pdf.cell(
                width,
                height,
                str(text),
                border=1,
                align="L" if index == 0 else "R",
            )

        pdf.ln(height)

    draw(headers, bold=True)

    for row in rows:
        draw([
            month_name(lang, row["month"]),
            fmt(lang, row["consumption_kwh"], 0),
            fmt(lang, row["generation_kwh"], 0),
            fmt(lang, row["bill_before_bdt"], 0),
            fmt(lang, row["bill_after_bdt"], 0),
            fmt(lang, row["payout_bdt"], 0),
        ])


def _build_assessment_summary(
    pdf,
    assessment,
    inputs,
    language="en",
):
    """Build the assessment summary before the detailed report."""

    lang = language
    assessment = assessment or {}
    inputs = inputs or {}

    def num(value, decimals=2):
        if value is None:
            return t(lang, "na")

        return fmt(lang, value, decimals)

    generation = assessment.get("generation", {})
    cost = assessment.get("cost", {})
    electricity = assessment.get("electricity", {})
    energy = assessment.get("energy_assessment") or {}
    savings = assessment.get("savings") or {}
    net_info = assessment.get("net_metering_info") or {}

    capacity = assessment.get("solar_capacity_kw")
    monthly_generation = generation.get("monthly_generation_kwh")
    monthly_consumption = electricity.get("monthly_consumption_kwh")
    total_cost = cost.get("total_cost_bdt")

    kwh = t(lang, "kwh", n="{}")
    kw = t(lang, "kw", n="{}")

    pdf.section_title(t(lang, "pdf_summary"), size=15)

    summary_rows = [
        (t(lang, "pdf_capacity"), kw.format(num(capacity))),
        (t(lang, "pdf_generation"), kwh.format(num(monthly_generation))),
        (t(lang, "pdf_cost"), f"৳{num(total_cost, 0)}"),
        (t(lang, "pdf_consumption"), kwh.format(num(monthly_consumption))),
    ]

    if savings.get("monthly_savings_bdt") is not None:
        summary_rows.append(
            (t(lang, "pdf_savings"), f"৳{num(savings['monthly_savings_bdt'], 0)}")
        )
        summary_rows.append(
            (t(lang, "pdf_annual_savings"), f"৳{num(savings['annual_savings_bdt'], 0)}")
        )

    if savings.get("annual_payout_bdt"):
        summary_rows.append(
            (t(lang, "pdf_surplus_paid"), f"৳{num(savings['annual_payout_bdt'], 0)}")
        )

    if savings.get("payback_years") is not None:
        summary_rows.append(
            (
                t(lang, "pdf_payback"),
                t(lang, "years", n=savings["payback_years"]).replace(
                    str(savings["payback_years"]),
                    num(savings["payback_years"], 1),
                ),
            )
        )

    for label, value in summary_rows:
        pdf.bordered_key_value(label, value)

    # ---- month by month ----
    monthly = assessment.get("monthly") or []

    if monthly:
        pdf.ln(3)
        pdf.section_title(t(lang, "pdf_monthly"), size=12)
        _monthly_table(pdf, monthly, lang)

    # ---- energy ----
    pdf.ln(3)
    pdf.section_title(t(lang, "pdf_energy"), size=12)

    if monthly_generation is not None:
        pdf.key_value(
            t(lang, "pdf_est_gen"), kwh.format(num(monthly_generation))
        )

    if monthly_consumption is not None:
        pdf.key_value(
            t(lang, "pdf_est_cons"), kwh.format(num(monthly_consumption))
        )

    # Same status the app shows (with its 5% balance tolerance).
    status = energy.get("status")

    if status == "potential_surplus":
        pdf.key_value(
            t(lang, "pdf_surplus"),
            kwh.format(num(energy.get("monthly_surplus_kwh"))),
        )
    elif status == "potential_shortfall":
        pdf.key_value(
            t(lang, "pdf_shortfall"),
            kwh.format(num(energy.get("monthly_shortfall_kwh"))),
        )
    elif status == "approximately_balanced":
        pdf.key_value(
            t(lang, "pdf_balance"), t(lang, "pdf_balanced")
        )

    # ---- inputs ----
    pdf.ln(3)
    pdf.section_title(t(lang, "pdf_details"), size=12)

    details = [
        (t(lang, "pdf_location"), inputs.get("location")),
        (
            t(lang, "pdf_bill"),
            f"৳{num(inputs['monthly_bill_bdt'], 0)}"
            if inputs.get("monthly_bill_bdt") is not None
            else None,
        ),
        (
            t(lang, "pdf_roof"),
            f"{num(inputs['roof_area_sqm'])} m²"
            if inputs.get("roof_area_sqm") is not None
            else None,
        ),
        (
            t(lang, "pdf_load"),
            kw.format(num(net_info["sanctioned_load_kw"]))
            if net_info.get("sanctioned_load_kw") is not None
            else None,
        ),
        (
            t(lang, "pdf_net_metering"),
            t(lang, "pdf_on" if net_info.get("enabled") else "pdf_off")
            if net_info
            else None,
        ),
        (
            t(lang, "pdf_battery"),
            t(lang, "pdf_required" if inputs.get("needs_battery") else "pdf_not_required")
            if inputs.get("needs_battery") is not None
            else None,
        ),
    ]

    if inputs.get("needs_battery"):
        if inputs.get("backup_load_kw") is not None:
            details.append(
                (t(lang, "pdf_backup_load"), kw.format(num(inputs["backup_load_kw"])))
            )

        if inputs.get("backup_hours") is not None:
            details.append(
                (
                    t(lang, "pdf_backup_hours"),
                    t(lang, "pdf_hours", n=0).replace(
                        digits(lang, "0"), num(inputs["backup_hours"])
                    ),
                )
            )

    for label, value in details:
        if value is not None:
            pdf.bordered_key_value(label, value)

    pdf.ln(3)
    pdf.line(
        pdf.l_margin,
        pdf.get_y(),
        pdf.w - pdf.r_margin,
        pdf.get_y(),
    )
    pdf.ln(3)

    pdf.section_title(t(lang, "pdf_report"), size=12)


# ==========================================================
# PDF GENERATION
# ==========================================================

def generate_solar_report_pdf(
    report: str,
    assessment: dict | None = None,
    assessment_inputs: dict | None = None,
    language: str = "en",
) -> bytes:
    """
    Generate an A4 PDF containing:
    1. Assessment summary.
    2. Energy assessment.
    3. Assessment inputs.
    4. Detailed feasibility report.

    Returns bytes for Streamlit's download button.
    """

    if not isinstance(report, str) or not report.strip():
        raise ValueError(
            "Cannot generate a PDF from an empty report."
        )

    _validate_fonts()

    pdf = SolarReportPDF(
        orientation="P",
        unit="mm",
        format="A4",
    )

    pdf.set_margins(
        left=18,
        top=15,
        right=18,
    )
    pdf.set_auto_page_break(
        auto=True,
        margin=18,
    )

    # Register embedded Unicode fonts.
    pdf.add_font(
        family="Noto",
        style="",
        fname=str(REGULAR_FONT),
    )

    pdf.add_font(
        family="Noto",
        style="B",
        fname=str(BOLD_FONT),
    )

    # Latin fallback for glyphs the Bengali font does not contain.
    if _latin_fonts_available():
        pdf.add_font(
            family="NotoLatin", style="", fname=str(LATIN_REGULAR_FONT)
        )
        pdf.add_font(
            family="NotoLatin", style="B", fname=str(LATIN_BOLD_FONT)
        )
        pdf.set_fallback_fonts(["NotoLatin"], exact_match=True)

    # Enable HarfBuzz shaping for Bangla conjuncts and vowel signs.
    pdf.set_text_shaping(
        use_shaping_engine=True,
        script="Beng",
        language="ben",
    )

    pdf.language = language

    pdf.set_title(t(language, "pdf_title"))
    pdf.set_author("Bangla Solar AI")

    pdf.add_page()

    _build_assessment_summary(
        pdf=pdf,
        assessment=assessment,
        inputs=assessment_inputs,
        language=language,
    )

    _markdown_to_pdf(
        pdf=pdf,
        report=report,
    )

    # fpdf2 returns PDF data as a bytearray.
    return bytes(pdf.output())
