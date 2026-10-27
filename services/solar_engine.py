from datetime import date

from tools.battery_sizing import calculate_battery_size
from tools.bill_analysis import estimate_monthly_consumption
from tools.config import assumptions_summary, resolve_assumptions
from tools.cost_estimation import estimate_solar_cost
from tools.pv_yield import get_location_yield
from tools.solar_economics import (
    calculate_monthly_economics,
    incentive_is_eligible,
)
from tools.system_sizing import size_solar_system


# Generation within this share of consumption counts as "balanced".
BALANCE_TOLERANCE = 0.05


def _monthly_consumption(average_kwh: float, factors: list[float]) -> list[float]:
    """Spread the average month over the year using the seasonal factors
    (rescaled so they average 1, which keeps the yearly total unchanged)."""

    mean = sum(factors) / len(factors)
    return [average_kwh * f / mean for f in factors]


def assess_solar_feasibility(
    monthly_bill_bdt: float,
    roof_area_sqm: float,
    location: str,
    needs_battery: bool = False,
    backup_load_kw: float = 0.5,
    backup_hours: float = 4.0,
    target_offset_fraction: float | None = None,
    overrides: dict | None = None,
    use_net_metering: bool | None = None,
    today: date | None = None,
) -> dict:
    """Create a preliminary, location-aware solar feasibility assessment.

    The system is sized to offset the household's consumption (limited by
    the roof), costed, and run through a twelve-month net-metering bill
    model to estimate savings and payback.

    All assumptions come from data/assumptions.json. `overrides` lets the
    caller replace specific values (for example a real installer quote),
    using keys such as "costs.solar_cost_per_kw_bdt".
    """

    if monthly_bill_bdt <= 0:
        raise ValueError("Monthly bill must be greater than zero.")

    if roof_area_sqm <= 0:
        raise ValueError("Roof area must be greater than zero.")

    if not location or not location.strip():
        raise ValueError("Location is required.")

    # 0. Resolve assumptions once (file values + user overrides).
    cfg = resolve_assumptions(overrides)
    net_cfg = cfg["net_metering"]

    if use_net_metering is None:
        use_net_metering = bool(net_cfg["enabled_by_default"])

    # 1. Consumption from the bill, using the slab tariff and demand charge.
    bill = estimate_monthly_consumption(monthly_bill_bdt, cfg=cfg)
    monthly_consumption_kwh = bill["monthly_consumption_kwh"]

    consumption_by_month = _monthly_consumption(
        monthly_consumption_kwh,
        cfg["profile"]["monthly_consumption_factors"],
    )

    # 2. Location-specific yield per kW (cached, shared with the agent).
    place = get_location_yield(location, cfg=cfg)
    yearly_yield_per_kw = place["yearly_kwh_per_kw"]

    profile = place.get("monthly_kwh_per_kw")
    has_monthly_profile = profile is not None

    if not has_monthly_profile:
        profile = [yearly_yield_per_kw / 12] * 12

    # 3. Size from roof AND consumption.
    sizing = size_solar_system(
        roof_area_sqm=roof_area_sqm,
        monthly_consumption_kwh=monthly_consumption_kwh,
        yearly_yield_kwh_per_kw=yearly_yield_per_kw,
        target_offset_fraction=target_offset_fraction,
        cfg=cfg,
    )

    solar_capacity_kw = sizing["recommended_capacity_kw"]

    # 4. Generation for that system, month by month.
    generation_by_month = [solar_capacity_kw * per_kw for per_kw in profile]
    estimated_annual_kwh = sum(generation_by_month)
    monthly_generation_kwh = estimated_annual_kwh / 12

    generation = {
        "capacity_kw": solar_capacity_kw,
        "yearly_yield_kwh_per_kw": round(yearly_yield_per_kw, 2),
        "daily_generation_kwh": round(estimated_annual_kwh / 365, 2),
        "monthly_generation_kwh": round(monthly_generation_kwh, 2),
        "yearly_generation_kwh": round(estimated_annual_kwh, 2),
        "has_monthly_profile": has_monthly_profile,
        "data_source": place["data_source"],
        "is_estimate": True,
    }

    # 5. Energy balance (yearly average), with a tolerance.
    energy_balance_kwh = round(
        monthly_generation_kwh - monthly_consumption_kwh, 2
    )

    if energy_balance_kwh > BALANCE_TOLERANCE * monthly_consumption_kwh:
        energy_assessment = {
            "status": "potential_surplus",
            "monthly_surplus_kwh": energy_balance_kwh,
            "message": (
                "Estimated solar generation exceeds "
                "estimated household consumption."
            ),
        }
    elif energy_balance_kwh < -BALANCE_TOLERANCE * monthly_consumption_kwh:
        energy_assessment = {
            "status": "potential_shortfall",
            "monthly_shortfall_kwh": abs(energy_balance_kwh),
            "message": (
                "Estimated solar generation is below "
                "estimated household consumption."
            ),
        }
    else:
        energy_assessment = {
            "status": "approximately_balanced",
            "monthly_difference_kwh": energy_balance_kwh,
            "message": (
                "Estimated solar generation approximately "
                "matches household consumption."
            ),
        }

    # 6. Optional battery.
    battery = None

    if needs_battery:
        battery = calculate_battery_size(
            load_kw=backup_load_kw,
            backup_hours=backup_hours,
            cfg=cfg,
        )

    battery_capacity_kwh = battery["battery_capacity_kwh"] if battery else 0

    # 7. Cost.
    cost = estimate_solar_cost(
        capacity_kw=solar_capacity_kw,
        battery_capacity_kwh=battery_capacity_kwh,
        cfg=cfg,
    )

    # 8. Net metering rules and the twelve-month bill model. Payback is on
    #    the solar cost; a backup battery does not reduce the bill, so its
    #    effect is reported separately.
    incentive_eligible = incentive_is_eligible(cfg, needs_battery, today)

    savings = calculate_monthly_economics(
        consumption_kwh_by_month=consumption_by_month,
        generation_kwh_by_month=generation_by_month,
        solar_cost_bdt=cost["solar_cost_bdt"],
        battery_cost_bdt=cost["battery_cost_bdt"],
        net_metering=use_net_metering,
        incentive_eligible=incentive_eligible,
        cfg=cfg,
    )

    sanctioned_load_kw = cfg["tariff"]["sanctioned_load_kw"]
    max_net_metered_kw = (
        sanctioned_load_kw
        * net_cfg["max_capacity_fraction_of_sanctioned_load"]
    )

    net_metering_info = {
        "enabled": use_net_metering,
        "incentive_eligible": bool(use_net_metering and incentive_eligible),
        "incentive_needs_battery": net_cfg["incentive_requires_battery"],
        "incentive_install_deadline": net_cfg["incentive_install_deadline"],
        "incentive_valid_until": net_cfg["incentive_valid_until"],
        "surplus_rate_bdt_per_kwh": savings["surplus_rate_bdt_per_kwh"],
        "sanctioned_load_kw": sanctioned_load_kw,
        "max_net_metered_kw": round(max_net_metered_kw, 2),
        "within_sanctioned_load": solar_capacity_kw <= max_net_metered_kw,
    }

    # 9. Limitations (fixed wording: translated in report_service).
    limitations = [
        "Solar generation is estimated using PVGIS data "
        "for the resolved coordinates.",
        "Roof shading, orientation, tilt, and structural "
        "suitability have not been inspected.",
        "Electricity consumption is estimated from your bill using the "
        "BERC residential slab tariff, the demand charge for your "
        "sanctioned load and VAT; meter rent and rebates are not "
        "included.",
        "Equipment costs are market estimates, not verified "
        "current quotations.",
        "Actual output depends on installation and "
        "weather conditions.",
        "Roof capacity is estimated from an assumed panel area per kW "
        "and usable roof fraction (see the assumptions used).",
        "Payback ignores tariff changes, panel degradation, "
        "maintenance, financing, and battery replacement.",
        "Every month is assumed to use the same amount of electricity "
        "unless a seasonal pattern is set in the assumptions.",
    ]

    if has_monthly_profile:
        limitations.append(
            "Monthly generation follows the PVGIS typical-weather "
            "profile; real months will vary."
        )
    else:
        limitations.append(
            "Annual generation divided by 12 is an average, "
            "not a month-specific forecast."
        )

    if use_net_metering:
        limitations.append(
            "Net metering is modelled as monthly netting with credit "
            "carried forward and settled in the settlement months; "
            "actual rules and rates may differ by distribution company."
        )
        limitations.append(
            "Surplus is paid at an estimated bulk rate; confirm the "
            "rate with your distribution company."
        )

        if net_metering_info["incentive_eligible"]:
            limitations.append(
                "The surplus incentive rate applies only to eligible "
                "battery-backed systems installed before the scheme "
                "deadline, and is not guaranteed."
            )

        if not net_metering_info["within_sanctioned_load"]:
            limitations.append(
                "The system is larger than your sanctioned load allows "
                "under net metering; you may need to apply for a "
                "load increase."
            )
    else:
        limitations.append(
            "Without net metering, surplus power is assumed to have "
            "no value."
        )

    assumptions = assumptions_summary(cfg, today)

    if assumptions["warnings"]:
        limitations.append(
            "Some assumptions are unverified or may be out of date; "
            "verify prices and tariffs before deciding."
        )

    if sizing["limiting_factor"] == "roof_area":
        limitations.append(
            "The system size is limited by available roof area, "
            "so it will not cover all household consumption."
        )
    else:
        limitations.append(
            "The system is sized to cover average household "
            "consumption; the roof could hold a larger system."
        )

    return {
        "location": place["location"],
        "latitude": place["latitude"],
        "longitude": place["longitude"],
        "energy_assessment": energy_assessment,
        "roof_area_sqm": roof_area_sqm,
        "usable_roof_area_sqm": sizing["usable_roof_area_sqm"],
        "solar_capacity_kw": solar_capacity_kw,
        "sizing": sizing,
        "electricity": bill,
        "generation": generation,
        "solar_resource": place["solar_resource"],
        "battery": battery,
        "cost": cost,
        "savings": savings,
        "monthly": savings["monthly"],
        "net_metering_info": net_metering_info,
        "assumptions": assumptions,
        "limitations": limitations,
    }
