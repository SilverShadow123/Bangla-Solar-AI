"""Month-by-month bill savings and payback, with Bangladesh net metering.

Net metering is modelled the way the Net Metering Guidelines describe it:

* Exports and imports are netted over the billing month. If the month's
  consumption is above the solar generation, you pay for the difference
  (after using any banked credit).
* If solar generation is above consumption, the extra units are banked as
  credit and carried into later months, where they offset consumption
  at the normal slab prices.
* At each settlement month, any credit still banked is paid out in cash,
  at the standard bulk rate or, for eligible battery systems, at the
  incentive rate. The bank then restarts from zero.

The fixed demand charge and VAT are paid every month regardless.
"""

from datetime import date

from tools.config import resolve_assumptions
from tools.tariff import bill_for_kwh

MONTHS = 12


def incentive_is_eligible(
    cfg: dict,
    needs_battery: bool,
    today: date | None = None,
) -> bool:
    """Whether the Tk/unit surplus incentive applies to a new system."""

    net = cfg["net_metering"]
    today = today or date.today()

    if net["incentive_requires_battery"] and not needs_battery:
        return False

    return today <= date.fromisoformat(net["incentive_install_deadline"])


def surplus_rate_bdt(cfg: dict, incentive_eligible: bool) -> float:
    net = cfg["net_metering"]

    return (
        net["incentive_rate_bdt_per_kwh"]
        if incentive_eligible
        else net["standard_surplus_rate_bdt_per_kwh"]
    )


def calculate_monthly_economics(
    consumption_kwh_by_month: list[float],
    generation_kwh_by_month: list[float],
    solar_cost_bdt: float,
    battery_cost_bdt: float = 0.0,
    net_metering: bool = True,
    incentive_eligible: bool = False,
    cfg: dict | None = None,
) -> dict:
    """Twelve-month bills before and after solar, with savings and payback."""

    if (
        len(consumption_kwh_by_month) != MONTHS
        or len(generation_kwh_by_month) != MONTHS
    ):
        raise ValueError("Provide 12 monthly values (January to December).")

    if any(c < 0 for c in consumption_kwh_by_month) or any(
        g < 0 for g in generation_kwh_by_month
    ):
        raise ValueError("Monthly energy values cannot be negative.")

    if sum(consumption_kwh_by_month) <= 0:
        raise ValueError("Monthly consumption must be greater than zero.")

    if solar_cost_bdt <= 0:
        raise ValueError("Solar cost must be greater than zero.")

    if battery_cost_bdt < 0:
        raise ValueError("Battery cost cannot be negative.")

    cfg = cfg if cfg is not None else resolve_assumptions()

    settlement_months = set(cfg["net_metering"]["settlement_months"])
    rate = surplus_rate_bdt(cfg, incentive_eligible)

    bank = 0.0
    rows = []

    for index in range(MONTHS):
        month = index + 1
        consumption = consumption_kwh_by_month[index]
        generation = generation_kwh_by_month[index]
        net = consumption - generation

        if net_metering:
            if net >= 0:
                used_credit = min(bank, net)
                bank -= used_credit
                billed = net - used_credit
            else:
                bank += -net
                billed = 0.0
        else:
            # No net meter: only generation used on site reduces the bill,
            # and surplus has no value.
            billed = max(net, 0.0)

        payout = 0.0
        paid_units = 0.0

        if net_metering and month in settlement_months and bank > 0:
            paid_units = bank
            payout = bank * rate
            bank = 0.0

        bill_before = bill_for_kwh(consumption, cfg)
        bill_after = bill_for_kwh(billed, cfg)

        rows.append({
            "month": month,
            "consumption_kwh": round(consumption, 2),
            "generation_kwh": round(generation, 2),
            "billed_kwh": round(billed, 2),
            "credit_balance_kwh": round(bank, 2),
            "bill_before_bdt": round(bill_before, 2),
            "bill_after_bdt": round(bill_after, 2),
            "payout_bdt": round(payout, 2),
            "paid_units_kwh": round(paid_units, 2),
            "savings_bdt": round(bill_before - bill_after + payout, 2),
        })

    total_consumption = sum(r["consumption_kwh"] for r in rows)
    total_billed = sum(r["billed_kwh"] for r in rows)
    annual_before = sum(r["bill_before_bdt"] for r in rows)
    annual_after = sum(r["bill_after_bdt"] for r in rows)
    annual_payout = sum(r["payout_bdt"] for r in rows)
    annual_savings = annual_before - annual_after + annual_payout
    paid_units = sum(r["paid_units_kwh"] for r in rows)

    if annual_savings > 0:
        payback = solar_cost_bdt / annual_savings
        payback_with_battery = (
            (solar_cost_bdt + battery_cost_bdt) / annual_savings
            if battery_cost_bdt > 0
            else None
        )
    else:
        payback = None
        payback_with_battery = None

    return {
        "monthly": rows,
        "net_metering": net_metering,
        "incentive_applied": bool(net_metering and incentive_eligible),
        "surplus_rate_bdt_per_kwh": rate if net_metering else None,
        "monthly_bill_before_bdt": round(annual_before / MONTHS, 2),
        "monthly_bill_after_bdt": round(
            (annual_after - annual_payout) / MONTHS, 2
        ),
        "monthly_savings_bdt": round(annual_savings / MONTHS, 2),
        "annual_bill_before_bdt": round(annual_before, 2),
        "annual_bill_after_bdt": round(annual_after, 2),
        "annual_payout_bdt": round(annual_payout, 2),
        "annual_savings_bdt": round(annual_savings, 2),
        "offset_kwh": round((total_consumption - total_billed) / MONTHS, 2),
        "offset_fraction": round(
            (total_consumption - total_billed) / total_consumption, 3
        ),
        "annual_exported_paid_kwh": round(paid_units, 2),
        "year_end_credit_kwh": round(bank, 2),
        "payback_years": (
            round(payback, 1) if payback is not None else None
        ),
        "payback_years_including_battery": (
            round(payback_with_battery, 1)
            if payback_with_battery is not None
            else None
        ),
        "tariff_basis": cfg["tariff"]["basis"],
        "is_estimate": True,
    }


def calculate_savings_and_payback(
    monthly_consumption_kwh: float,
    monthly_generation_kwh: float,
    solar_cost_bdt: float,
    battery_cost_bdt: float = 0.0,
    net_metering: bool = True,
    cfg: dict | None = None,
) -> dict:
    """Savings and payback for an average month repeated for a year.

    Used by the chat tool for quick what-ifs. The main assessment uses
    calculate_monthly_economics() with the real month-by-month profile.
    """

    if monthly_consumption_kwh <= 0:
        raise ValueError("Monthly consumption must be greater than zero.")

    if monthly_generation_kwh < 0:
        raise ValueError("Monthly generation cannot be negative.")

    cfg = cfg if cfg is not None else resolve_assumptions()

    return calculate_monthly_economics(
        consumption_kwh_by_month=[monthly_consumption_kwh] * MONTHS,
        generation_kwh_by_month=[monthly_generation_kwh] * MONTHS,
        solar_cost_bdt=solar_cost_bdt,
        battery_cost_bdt=battery_cost_bdt,
        net_metering=net_metering,
        incentive_eligible=incentive_is_eligible(
            cfg, needs_battery=battery_cost_bdt > 0
        ),
        cfg=cfg,
    )
