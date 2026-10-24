from tools.tariff import TARIFF_BASIS, kwh_from_bill


def estimate_monthly_consumption(
    monthly_bill_bdt: float,
    average_rate_bdt_per_kwh: float | None = None,
) -> dict:
    """Estimate monthly consumption from a bill.

    By default the BERC residential slab tariff is inverted. Passing
    average_rate_bdt_per_kwh switches to a flat-rate estimate.
    """

    if monthly_bill_bdt < 0:
        raise ValueError("Monthly bill cannot be negative.")

    if average_rate_bdt_per_kwh is not None:
        if average_rate_bdt_per_kwh <= 0:
            raise ValueError("Average electricity rate must be positive.")

        monthly_consumption = monthly_bill_bdt / average_rate_bdt_per_kwh
        basis = f"flat rate of {average_rate_bdt_per_kwh} BDT/kWh"
    else:
        monthly_consumption = kwh_from_bill(monthly_bill_bdt)
        basis = TARIFF_BASIS

    effective_rate = (
        monthly_bill_bdt / monthly_consumption
        if monthly_consumption > 0
        else None
    )

    return {
        "monthly_bill_bdt": round(monthly_bill_bdt, 2),
        "assumed_rate_bdt_per_kwh": (
            round(effective_rate, 2) if effective_rate else None
        ),
        "monthly_consumption_kwh": round(monthly_consumption, 2),
        "daily_consumption_kwh": round(monthly_consumption / 30, 2),
        "tariff_basis": basis,
        "is_estimate": True,
    }
