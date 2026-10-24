def estimate_solar_cost(
        capacity_kw: float,
        cost_per_kw_bdt: float = 80000.0,
        battery_capacity_kwh: float = 0.0,
        battery_cost_per_kwh_bdt: float = 30000.0,
) -> dict:
    if capacity_kw <= 0:
        raise ValueError("Solar capacity must be greater than zero.")

    if cost_per_kw_bdt <= 0:
        raise ValueError("Solar cost per kW must be positive.")

    if battery_capacity_kwh < 0:
        raise ValueError("Battery capacity cannot be negative.")

    if battery_capacity_kwh > 0 and battery_cost_per_kwh_bdt <= 0:
        raise ValueError("Battery cost per kWh must be positive.")

    solar_cost = capacity_kw * cost_per_kw_bdt

    battery_cost = (
            battery_capacity_kwh * battery_cost_per_kwh_bdt
    )

    total_cost = solar_cost + battery_cost

    return {
        "solar_capacity_kw": capacity_kw,
        "solar_cost_bdt": round(solar_cost, 2),
        "battery_capacity_kwh": battery_capacity_kwh,
        "battery_cost_bdt": round(battery_cost, 2),
        "total_cost_bdt": round(total_cost, 2),
        "is_estimate": True,
    }
