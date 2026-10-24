"""Size a rooftop system from roof area AND household consumption."""

USABLE_ROOF_FRACTION = 0.70

ROOF_AREA_PER_KW_SQM = 5.5


def size_solar_system(
    roof_area_sqm: float,
    monthly_consumption_kwh: float,
    yearly_yield_kwh_per_kw: float,
    target_offset_fraction: float = 1.0,
) -> dict:
    """Recommend a capacity: enough to offset the target share of
    consumption, but never more than the roof can hold."""

    if roof_area_sqm <= 0:
        raise ValueError("Roof area must be greater than zero.")

    if monthly_consumption_kwh <= 0:
        raise ValueError("Monthly consumption must be greater than zero.")

    if yearly_yield_kwh_per_kw <= 0:
        raise ValueError("Yearly yield per kW must be greater than zero.")

    if not 0 < target_offset_fraction <= 1:
        raise ValueError("Target offset must be between 0 and 1.")

    usable_roof_area = roof_area_sqm * USABLE_ROOF_FRACTION
    roof_limit_kw = usable_roof_area / ROOF_AREA_PER_KW_SQM

    demand_kw = (
        monthly_consumption_kwh
        * 12
        * target_offset_fraction
        / yearly_yield_kwh_per_kw
    )

    limiting_factor = (
        "roof_area" if roof_limit_kw < demand_kw else "consumption"
    )

    recommended_kw = round(min(roof_limit_kw, demand_kw), 2)

    if recommended_kw <= 0:
        raise ValueError(
            "Consumption or roof area is too small to size a system."
        )

    return {
        "usable_roof_area_sqm": round(usable_roof_area, 2),
        "roof_limit_kw": round(roof_limit_kw, 2),
        "demand_based_kw": round(demand_kw, 2),
        "recommended_capacity_kw": recommended_kw,
        "limiting_factor": limiting_factor,
        "target_offset_fraction": target_offset_fraction,
        "roof_area_per_kw_sqm": ROOF_AREA_PER_KW_SQM,
        "usable_roof_fraction": USABLE_ROOF_FRACTION,
    }
