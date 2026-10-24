
def calculate_solar_generation(
    capacity_kw: float,
    peak_sun_hours: float = 4.5,
    system_efficiency: float = 0.80,
) -> dict:

    if capacity_kw <= 0:
        raise ValueError("Solar capacity must be greater than zero.")

    if peak_sun_hours <= 0 or peak_sun_hours > 12:
        raise ValueError("Peak sun hours must be between 0 and 12.")

    if not 0 < system_efficiency <= 1:
        raise ValueError("Efficiency must be greater than 0 and at most 1.")

    daily_generation = (
        capacity_kw * peak_sun_hours * system_efficiency
    )

    monthly_generation = daily_generation * 30

    return {
        "capacity_kw": capacity_kw,
        "daily_generation_kwh": round(daily_generation, 2),
        "monthly_generation_kwh": round(monthly_generation, 2),
        "peak_sun_hours": peak_sun_hours,
        "system_efficiency": system_efficiency,
        "is_estimate": True,
    }
