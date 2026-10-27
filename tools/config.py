"""Load, validate and resolve the assumptions stored in data/assumptions.json.

Every number the calculations depend on lives in that file, together with
its source, date and a "verified" flag. Edit the file (no restart needed)
to update a tariff or price. Set SOLAR_ASSUMPTIONS_PATH to use another file.
"""

import copy
import json
import os
from datetime import date
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATH = PROJECT_ROOT / "data" / "assumptions.json"

# Keys that describe a section rather than being calculation inputs.
META_KEYS = {
    "label",
    "label_bn",
    "basis",
    "source_url",
    "cross_check_url",
    "as_of",
    "verified",
    "estimate",
    "note",
    "note_bn",
    "replaceable_by_quote",
}

# Values a user may override (sidebar or chat), with inclusive bounds.
ALLOWED_OVERRIDES = {
    "costs.solar_cost_per_kw_bdt": (1, 10_000_000),
    "costs.battery_cost_per_kwh_bdt": (1, 10_000_000),
    "tariff.vat_rate": (0, 1),
    "tariff.sanctioned_load_kw": (0.1, 50),
    "tariff.demand_charge_per_kw_bdt": (0, 1_000),
    "net_metering.standard_surplus_rate_bdt_per_kwh": (0, 100),
    "roof.area_per_kw_sqm": (2, 30),
    "roof.usable_fraction": (0.05, 1),
    "sizing.target_offset_fraction": (0.05, 1),
    "battery.depth_of_discharge": (0.1, 1),
    "battery.inverter_efficiency": (0.5, 1),
    "pvgis.system_loss_percent": (0, 60),
}

REQUIRED_KEYS = {
    "tariff": [
        "basis",
        "lifeline_limit_kwh",
        "lifeline_rate_bdt",
        "slabs",
        "vat_rate",
        "demand_charge_per_kw_bdt",
        "sanctioned_load_kw",
    ],
    "net_metering": [
        "enabled_by_default",
        "settlement_months",
        "standard_surplus_rate_bdt_per_kwh",
        "incentive_rate_bdt_per_kwh",
        "incentive_requires_battery",
        "incentive_install_deadline",
        "incentive_valid_until",
        "max_capacity_fraction_of_sanctioned_load",
    ],
    "roof": ["usable_fraction", "area_per_kw_sqm"],
    "costs": ["solar_cost_per_kw_bdt", "battery_cost_per_kwh_bdt"],
    "battery": ["depth_of_discharge", "inverter_efficiency"],
    "pvgis": [
        "api_url",
        "timeout_seconds",
        "system_loss_percent",
        "angle_degrees",
        "aspect_degrees",
        "use_optimal_angles",
    ],
    "sizing": ["target_offset_fraction"],
    "profile": ["monthly_consumption_factors"],
}


class AssumptionsError(ValueError):
    """The assumptions file is missing, malformed, or an override is invalid."""


def _assumptions_path() -> Path:
    return Path(os.getenv("SOLAR_ASSUMPTIONS_PATH", str(DEFAULT_PATH)))


def _validate(data: dict, path: Path) -> None:
    where = f"Assumptions file {path}"

    if not isinstance(data.get("max_age_days"), (int, float)):
        raise AssumptionsError(f"{where}: 'max_age_days' must be a number.")

    for section, keys in REQUIRED_KEYS.items():
        if not isinstance(data.get(section), dict):
            raise AssumptionsError(f"{where}: missing section '{section}'.")

        for key in keys:
            if key not in data[section]:
                raise AssumptionsError(
                    f"{where}: missing '{key}' in section '{section}'."
                )

    # ---- tariff slabs ----
    slabs = data["tariff"]["slabs"]

    if not isinstance(slabs, list) or not slabs:
        raise AssumptionsError(f"{where}: tariff.slabs must be a list.")

    previous = 0

    for index, slab in enumerate(slabs):
        is_last = index == len(slabs) - 1

        if (
            not isinstance(slab, dict)
            or "up_to_kwh" not in slab
            or "rate_bdt" not in slab
        ):
            raise AssumptionsError(
                f"{where}: each slab needs 'up_to_kwh' and 'rate_bdt'."
            )

        if slab["rate_bdt"] <= 0:
            raise AssumptionsError(f"{where}: slab rates must be positive.")

        upper = slab["up_to_kwh"]

        if is_last:
            if upper is not None:
                raise AssumptionsError(
                    f"{where}: the last slab must have up_to_kwh = null."
                )
        else:
            if upper is None or upper <= previous:
                raise AssumptionsError(
                    f"{where}: slab limits must be increasing, and only "
                    "the last slab may be null."
                )

            previous = upper

    # ---- seasonal consumption profile ----
    factors = data["profile"]["monthly_consumption_factors"]

    if (
        not isinstance(factors, list)
        or len(factors) != 12
        or any(
            not isinstance(f, (int, float)) or f <= 0 for f in factors
        )
    ):
        raise AssumptionsError(
            f"{where}: profile.monthly_consumption_factors must be "
            "12 positive numbers (January to December)."
        )

    # ---- net metering ----
    net = data["net_metering"]
    months = net["settlement_months"]

    if (
        not isinstance(months, list)
        or not months
        or any(not isinstance(m, int) or not 1 <= m <= 12 for m in months)
    ):
        raise AssumptionsError(
            f"{where}: net_metering.settlement_months must be a list of "
            "month numbers from 1 to 12."
        )

    for key in ("incentive_install_deadline", "incentive_valid_until"):
        try:
            date.fromisoformat(net[key])
        except (TypeError, ValueError) as error:
            raise AssumptionsError(
                f"{where}: net_metering.{key} must be a YYYY-MM-DD date."
            ) from error


@lru_cache(maxsize=4)
def _parse(path_str: str, mtime_ns: int) -> dict:
    """Parse and validate the file. mtime_ns is part of the cache key, so
    editing the file takes effect without restarting the app."""

    path = Path(path_str)

    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as error:
        raise AssumptionsError(
            f"Assumptions file {path} is not valid JSON: {error}"
        ) from error

    _validate(data, path)
    return data


def _load_base() -> dict:
    path = _assumptions_path()

    try:
        mtime_ns = path.stat().st_mtime_ns
    except OSError as error:
        raise AssumptionsError(
            f"Assumptions file not found: {path}"
        ) from error

    return _parse(str(path), mtime_ns)


def apply_overrides(cfg: dict, overrides: dict | None) -> dict:
    """Apply validated user overrides in place; returns what was applied."""

    applied = {}

    for key, value in (overrides or {}).items():
        if key not in ALLOWED_OVERRIDES:
            allowed = ", ".join(sorted(ALLOWED_OVERRIDES))
            raise AssumptionsError(
                f"Unknown assumption override '{key}'. Allowed: {allowed}."
            )

        try:
            number = float(value)
        except (TypeError, ValueError) as error:
            raise AssumptionsError(
                f"Override '{key}' must be a number."
            ) from error

        low, high = ALLOWED_OVERRIDES[key]

        if not low <= number <= high:
            raise AssumptionsError(
                f"Override '{key}' must be between {low} and {high}."
            )

        section, name = key.split(".", 1)
        cfg[section][name] = number
        applied[key] = number

    return applied


def resolve_assumptions(overrides: dict | None = None) -> dict:
    """Return a private copy of the assumptions with overrides applied.

    cfg["_overrides"] records which values the user changed.
    """

    cfg = copy.deepcopy(_load_base())
    cfg["_overrides"] = apply_overrides(cfg, overrides)
    return cfg


def _sections(cfg: dict):
    for name, section in cfg.items():
        if not name.startswith("_") and isinstance(section, dict):
            yield name, section


def data_warning_items(cfg: dict, today: date | None = None) -> list[dict]:
    """Structured warnings about unverified, estimated or out-of-date data.

    Each item has a `code` ("unverified", "estimate", "stale", "bad_date")
    so the UI can word it in any language.
    """

    today = today or date.today()
    max_age = cfg["max_age_days"]
    overrides = cfg.get("_overrides", {})
    items = []

    for name, section in _sections(cfg):
        label = section.get("label", name)
        note = section.get("note", "")

        base = {
            "section": name,
            "label": label,
            "label_bn": section.get("label_bn") or label,
            "note": note,
            "note_bn": section.get("note_bn") or note,
            "as_of": section.get("as_of"),
            "source_url": section.get("source_url"),
        }

        # A section a real quote can replace is fine once every one of
        # its values has been supplied by the user.
        if section.get("replaceable_by_quote"):
            keys = [k for k in ALLOWED_OVERRIDES if k.startswith(f"{name}.")]

            if keys and all(k in overrides for k in keys):
                continue

        if section.get("verified") is False:
            items.append({**base, "code": "unverified"})
            continue

        if section.get("estimate"):
            items.append({**base, "code": "estimate"})

        as_of = section.get("as_of")

        if as_of:
            try:
                age = (today - date.fromisoformat(as_of)).days
            except ValueError:
                items.append({**base, "code": "bad_date"})
                continue

            if age > max_age:
                items.append({**base, "code": "stale", "age_days": age})

    return items


def format_warning(item: dict) -> str:
    """English one-line text for a warning item (used for the agent)."""

    code = item["code"]

    if code == "unverified":
        return f"Unverified: {item['label']}. {item['note']}".strip()

    if code == "estimate":
        return f"Market estimate: {item['label']}. {item['note']}".strip()

    if code == "stale":
        hint = f" Check {item['source_url']}." if item.get("source_url") else ""
        return (
            f"Out of date: {item['label']} is {item['age_days']} days old "
            f"(as of {item['as_of']}).{hint}"
        )

    return (
        f"Unreadable date for {item['label']} ('{item['as_of']}'); "
        "use YYYY-MM-DD."
    )


def data_warnings(cfg: dict, today: date | None = None) -> list[str]:
    """Plain-language English warnings."""

    return [format_warning(item) for item in data_warning_items(cfg, today)]


def assumptions_summary(cfg: dict, today: date | None = None) -> dict:
    """Everything the UI and agent need to show which assumptions were used."""

    values = {}
    sources = {}

    for name, section in _sections(cfg):
        sources[name] = {
            "label": section.get("label", name),
            "label_bn": section.get("label_bn") or section.get("label", name),
            "as_of": section.get("as_of"),
            "verified": section.get("verified"),
            "estimate": section.get("estimate", False),
            "source_url": section.get("source_url"),
            "note": section.get("note"),
            "note_bn": section.get("note_bn"),
        }

        for key, value in section.items():
            if key in META_KEYS:
                continue

            values[f"{name}.{key}"] = value

    items = data_warning_items(cfg, today)

    return {
        "tariff_basis": cfg["tariff"]["basis"],
        "values": values,
        "sources": sources,
        "overrides": dict(cfg.get("_overrides", {})),
        "warning_items": items,
        "warnings": [format_warning(item) for item in items],
    }
