"""Bill savings and payback under the configured tariff."""

from tools.config import resolve_assumptions
from tools.tariff import bill_for_kwh


def calculate_savings_and_payback(
    monthly_consumption_kwh: float,
    monthly_generation_kwh: float,
    solar_cost_bdt: float,
    battery_cost_bdt: float = 0.0,
    cfg: dict | None = None,
) -> dict:
    """Estimate monthly savings and simple payback.

    Only generation up to the month's consumption offsets the bill;
    exported surplus is given no cash value (conservative). Solar output
    removes the highest-priced units first, because the tariff is
    incremental by slab.
    """

    if monthly_consumption_kwh <= 0:
        raise ValueError("Monthly consumption must be greater than zero.")

    if monthly_generation_kwh < 0:
        raise ValueError("Monthly generation cannot be negative.")

    if solar_cost_bdt <= 0:
        raise ValueError("Solar cost must be greater than zero.")

    if battery_cost_bdt < 0:
        raise ValueError("Battery cost cannot be negative.")

    cfg = cfg if cfg is not None else resolve_assumptions()

    offset_kwh = min(monthly_generation_kwh, monthly_consumption_kwh)

    bill_before = bill_for_kwh(monthly_consumption_kwh, cfg)
    bill_after = bill_for_kwh(monthly_consumption_kwh - offset_kwh, cfg)

    monthly_savings = bill_before - bill_after
    annual_savings = monthly_savings * 12

    if annual_savings > 0:
        payback_years = solar_cost_bdt / annual_savings
        payback_with_battery = (
            (solar_cost_bdt + battery_cost_bdt) / annual_savings
            if battery_cost_bdt > 0
            else None
        )
    else:
        payback_years = None
        payback_with_battery = None

    return {
        "monthly_bill_before_bdt": round(bill_before, 2),
        "monthly_bill_after_bdt": round(bill_after, 2),
        "monthly_savings_bdt": round(monthly_savings, 2),
        "annual_savings_bdt": round(annual_savings, 2),
        "offset_kwh": round(offset_kwh, 2),
        "offset_fraction": round(offset_kwh / monthly_consumption_kwh, 3),
        "unused_surplus_kwh": round(
            max(monthly_generation_kwh - monthly_consumption_kwh, 0.0), 2
        ),
        "payback_years": (
            round(payback_years, 1) if payback_years is not None else None
        ),
        "payback_years_including_battery": (
            round(payback_with_battery, 1)
            if payback_with_battery is not None
            else None
        ),
        "tariff_basis": cfg["tariff"]["basis"],
        "is_estimate": True,
    }
