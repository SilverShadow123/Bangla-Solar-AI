"""Electricity bill calculation.

All rates, slabs, VAT and the demand charge come from
data/assumptions.json (see tools/config.py). Functions take an optional
resolved config so callers can pass user overrides.
"""

from tools.config import resolve_assumptions


def _cfg(cfg):
    return cfg if cfg is not None else resolve_assumptions()


def demand_charge(cfg: dict | None = None) -> float:
    """Fixed monthly demand charge: rate per kW x sanctioned load."""

    tariff = _cfg(cfg)["tariff"]

    return tariff["demand_charge_per_kw_bdt"] * tariff["sanctioned_load_kw"]


def energy_charge(monthly_kwh: float, cfg: dict | None = None) -> float:
    """Energy charge in BDT for a month's consumption (before VAT)."""

    if monthly_kwh < 0:
        raise ValueError("Consumption cannot be negative.")

    if monthly_kwh == 0:
        return 0.0

    tariff = _cfg(cfg)["tariff"]

    # Lifeline: within the limit, every unit is charged at the lifeline
    # rate. Above it, the lifeline rate no longer applies.
    if monthly_kwh <= tariff["lifeline_limit_kwh"]:
        return monthly_kwh * tariff["lifeline_rate_bdt"]

    charge = 0.0
    lower = 0.0

    for slab in tariff["slabs"]:
        upper = slab["up_to_kwh"]
        top = monthly_kwh if upper is None else min(monthly_kwh, upper)

        if top > lower:
            charge += (top - lower) * slab["rate_bdt"]

        if upper is None or monthly_kwh <= upper:
            break

        lower = upper

    return charge


def bill_for_kwh(monthly_kwh: float, cfg: dict | None = None) -> float:
    """Total monthly bill in BDT for the given consumption."""

    cfg = _cfg(cfg)
    tariff = cfg["tariff"]

    # VAT applies to the energy charge plus the demand charge.
    return (
        energy_charge(monthly_kwh, cfg) + demand_charge(cfg)
    ) * (1 + tariff["vat_rate"])


def calculate_bill(monthly_kwh: float, cfg: dict | None = None) -> dict:
    """Bill with a breakdown, for use as an agent tool."""

    cfg = _cfg(cfg)
    tariff = cfg["tariff"]
    total = bill_for_kwh(monthly_kwh, cfg)

    return {
        "monthly_consumption_kwh": round(monthly_kwh, 2),
        "energy_charge_bdt": round(energy_charge(monthly_kwh, cfg), 2),
        "demand_charge_bdt": demand_charge(cfg),
        "sanctioned_load_kw": tariff["sanctioned_load_kw"],
        "vat_rate": tariff["vat_rate"],
        "total_bill_bdt": round(total, 2),
        "effective_rate_bdt_per_kwh": (
            round(total / monthly_kwh, 2) if monthly_kwh > 0 else None
        ),
        "tariff_basis": tariff["basis"],
        "is_estimate": True,
    }


def kwh_from_bill(monthly_bill_bdt: float, cfg: dict | None = None) -> float:
    """Invert the tariff: find the consumption that produces this bill.

    The bill is non-decreasing in consumption, so bisection works. If the
    bill is no more than the fixed charges, consumption is zero.
    """

    if monthly_bill_bdt < 0:
        raise ValueError("Monthly bill cannot be negative.")

    cfg = _cfg(cfg)

    if monthly_bill_bdt <= bill_for_kwh(0, cfg):
        return 0.0

    low = 0.0
    high = 100.0

    while bill_for_kwh(high, cfg) < monthly_bill_bdt:
        high *= 2

        if high > 1_000_000:
            raise ValueError("Monthly bill is unrealistically large.")

    for _ in range(80):
        mid = (low + high) / 2

        if bill_for_kwh(mid, cfg) < monthly_bill_bdt:
            low = mid
        else:
            high = mid

    return high
