def estimate_monthly_consumption(
    monthly_bill_bdt: float,
    average_rate_bdt_per_kwh: float = 10.0,
) -> dict:

    if monthly_bill_bdt < 0:
        raise ValueError("Monthly bill cannot be negative.")

    if average_rate_bdt_per_kwh <= 0:
        raise ValueError("Average electricity rate must be positive.")

    monthly_consumption = (
        monthly_bill_bdt / average_rate_bdt_per_kwh
    )

    daily_consumption = monthly_consumption / 30

    return {
        "monthly_bill_bdt": round(monthly_bill_bdt, 2),
        "assumed_rate_bdt_per_kwh": average_rate_bdt_per_kwh,
        "monthly_consumption_kwh": round(monthly_consumption, 2),
        "daily_consumption_kwh": round(daily_consumption, 2),
        "is_estimate": True,
    }
