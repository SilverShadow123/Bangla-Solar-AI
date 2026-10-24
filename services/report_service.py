
import io
import re
from pathlib import Path

from fpdf import FPDF


# ==========================================================
# FONT CONFIGURATION
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = PROJECT_ROOT / "assets" / "fonts"

REGULAR_FONT = FONT_DIR / "NotoSansBengali-Regular.ttf"
BOLD_FONT = FONT_DIR / "NotoSansBengali-Bold.ttf"


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

        disclaimer = (
            "এটি একটি প্রাথমিক অনুমান। ইনস্টলেশনের আগে "
            "যোগ্য সোলার পেশাজীবীর মাধ্যমে যাচাই করুন।"
        )

        limitation_translations = {
            "Solar generation is estimated using PVGIS data for the resolved coordinates.":
                "নির্ধারিত স্থানাঙ্কের জন্য PVGIS তথ্য ব্যবহার করে "
                "সৌরবিদ্যুৎ উৎপাদন অনুমান করা হয়েছে।",

            "Annual generation divided by 12 is an average, not a month-specific forecast.":
                "বার্ষিক উৎপাদনকে ১২ দিয়ে ভাগ করে মাসিক গড় নির্ণয় "
                "করা হয়েছে; এটি নির্দিষ্ট মাসের পূর্বাভাস নয়।",

            "Roof shading, orientation, tilt, and structural suitability have not been inspected.":
                "ছাদের ছায়া, দিক, ঢাল এবং কাঠামোগত উপযুক্ততা "
                "সরেজমিনে পরীক্ষা করা হয়নি।",

            "Electricity consumption is estimated using an assumed rate, not the actual tariff calculation.":
                "প্রকৃত বিদ্যুৎ ট্যারিফ হিসাব না করে একটি "
                "অনুমানভিত্তিক দর দিয়ে বিদ্যুৎ ব্যবহার নির্ণয় করা হয়েছে।",

            "Equipment costs are illustrative, not verified current quotations.":
                "সরঞ্জামের খরচ উদাহরণভিত্তিক; বর্তমান বাজারদরের "
                "যাচাইকৃত কোটেশন নয়।",

            "Actual output depends on installation and weather conditions.":
                "প্রকৃত উৎপাদন স্থাপনার ধরন ও আবহাওয়ার ওপর নির্ভর করবে।",

            "Solar generation uses assumed peak-sun hours and efficiency.":
                "সৌরবিদ্যুৎ উৎপাদন নির্ধারণে অনুমানভিত্তিক "
                "সান আওয়ার ও দক্ষতা ব্যবহার করা হয়েছে।",

            "Roof suitability and shading have not been inspected.":
                "ছাদের উপযুক্ততা ও ছায়ার অবস্থা পরীক্ষা করা হয়নি।",

            "Electricity consumption is estimated from an assumed rate.":
                "অনুমানভিত্তিক বিদ্যুৎদরের ভিত্তিতে বিদ্যুৎ ব্যবহার "
                "নির্ণয় করা হয়েছে।",

            "Equipment costs are illustrative, not current quotations.":
                "সরঞ্জামের খরচ উদাহরণভিত্তিক, বর্তমান বাজারের "
                "কোটেশন নয়।",

            "Location coordinates are not yet used in solar generation.":
                "সৌরবিদ্যুৎ উৎপাদনের হিসাবে এখনো অবস্থানের "
                "স্থানাঙ্ক ব্যবহার করা হয়নি।",
        }

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

    lines.extend(["", f"**Note:** {disclaimer}"])

    return "\n".join(lines)


# ==========================================================
# PDF DOCUMENT
# ==========================================================

class SolarReportPDF(FPDF):
    """A4 report with Unicode fonts and Bangla text shaping."""

    def header(self):
        self.set_font("Noto", style="B", size=9)
        self.cell(
            0,
            7,
            "Bangla Solar AI",
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
            f"Bangla Solar AI - Preliminary estimates | Page {self.page_no()}",
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

def _build_assessment_summary(
    pdf,
    assessment,
    inputs,
):
    """Build the assessment summary before the detailed report."""

    assessment = assessment or {}
    inputs = inputs or {}

    generation = assessment.get("generation", {})
    cost = assessment.get("cost", {})
    electricity = assessment.get("electricity", {})
    energy = assessment.get("energy_assessment") or {}

    capacity = assessment.get("solar_capacity_kw")
    monthly_generation = generation.get(
        "monthly_generation_kwh"
    )

    monthly_consumption = energy.get(
        "monthly_consumption_kwh",
        electricity.get("monthly_consumption_kwh"),
    )

    total_cost = cost.get("total_cost_bdt")

    pdf.section_title("Your Solar Assessment", size=15)

    summary_rows = [
        (
            "Solar Capacity",
            (
                f"{_format_number(capacity)} kW"
                if capacity is not None
                else "Not available"
            ),
        ),
        (
            "Monthly Generation",
            (
                f"{_format_number(monthly_generation)} kWh"
                if monthly_generation is not None
                else "Not available"
            ),
        ),
        (
            "Estimated Cost",
            (
                f"BDT {_format_number(total_cost, 0)}"
                if total_cost is not None
                else "Not available"
            ),
        ),
        (
            "Monthly Consumption",
            (
                f"{_format_number(monthly_consumption)} kWh"
                if monthly_consumption is not None
                else "Not available"
            ),
        ),
    ]

    for label, value in summary_rows:
        pdf.bordered_key_value(label, value)

    pdf.ln(3)
    pdf.section_title("Energy Assessment", size=12)

    if monthly_generation is not None:
        pdf.key_value(
            "Estimated Monthly Solar Generation",
            f"{_format_number(monthly_generation)} kWh",
        )

    if monthly_consumption is not None:
        pdf.key_value(
            "Estimated Monthly Consumption",
            f"{_format_number(monthly_consumption)} kWh",
        )

    surplus = energy.get("monthly_surplus_kwh")
    shortfall = energy.get("monthly_shortfall_kwh")

    if surplus is not None:
        pdf.key_value(
            "Estimated Monthly Surplus",
            f"{_format_number(surplus)} kWh",
        )

    elif shortfall is not None:
        pdf.key_value(
            "Estimated Monthly Shortfall",
            f"{_format_number(shortfall)} kWh",
        )

    elif (
        monthly_generation is not None
        and monthly_consumption is not None
    ):
        difference = (
            float(monthly_generation)
            - float(monthly_consumption)
        )

        label = (
            "Estimated Monthly Surplus"
            if difference >= 0
            else "Estimated Monthly Shortfall"
        )

        pdf.key_value(
            label,
            f"{_format_number(abs(difference))} kWh",
        )

    pdf.ln(3)
    pdf.section_title("Assessment Details", size=12)

    details = [
        ("Location", inputs.get("location")),
        (
            "Monthly Electricity Bill",
            (
                f"BDT {_format_number(inputs['monthly_bill_bdt'], 0)}"
                if inputs.get("monthly_bill_bdt") is not None
                else None
            ),
        ),
        (
            "Roof Area",
            (
                f"{_format_number(inputs['roof_area_sqm'])} m²"
                if inputs.get("roof_area_sqm") is not None
                else None
            ),
        ),
        (
            "Battery Backup",
            (
                "Required"
                if inputs.get("needs_battery")
                else "Not required"
            ) if inputs.get("needs_battery") is not None else None,
        ),
    ]

    if inputs.get("needs_battery"):
        if inputs.get("backup_load_kw") is not None:
            details.append((
                "Backup Load",
                f"{_format_number(inputs['backup_load_kw'])} kW",
            ))

        if inputs.get("backup_hours") is not None:
            details.append((
                "Backup Duration",
                f"{_format_number(inputs['backup_hours'])} hours",
            ))

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

    pdf.section_title("Feasibility Report", size=12)


# ==========================================================
# PDF GENERATION
# ==========================================================

def generate_solar_report_pdf(
    report: str,
    assessment: dict | None = None,
    assessment_inputs: dict | None = None,
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

    # Enable HarfBuzz shaping for Bangla conjuncts and vowel signs.
    pdf.set_text_shaping(
        use_shaping_engine=True,
        script="Beng",
        language="ben",
    )

    pdf.set_title(
        "Bangla Solar AI - Solar Feasibility Report"
    )
    pdf.set_author("Bangla Solar AI")

    pdf.add_page()

    _build_assessment_summary(
        pdf=pdf,
        assessment=assessment,
        inputs=assessment_inputs,
    )

    _markdown_to_pdf(
        pdf=pdf,
        report=report,
    )

    # fpdf2 returns PDF data as a bytearray.
    return bytes(pdf.output())
