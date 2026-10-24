from tools.battery_sizing import calculate_battery_size
from tools.bill_analysis import estimate_monthly_consumption
from tools.cost_estimation import estimate_solar_cost
from tools.pv_yield import get_location_yield
from tools.solar_economics import calculate_savings_and_payback
from tools.system_sizing import size_solar_system


BALANCE_TOLERANCE = 0.05


def assess_solar_feasibility(
    monthly_bill_bdt: float,
    roof_area_sqm: float,
    location: str,
    needs_battery: bool = False,
    backup_load_kw: float = 0.5,
    backup_hours: float = 4.0,
    target_offset_fraction: float = 1.0,
) -> dict:
    """Create a preliminary, location-aware solar feasibility assessment.

    The system is sized to offset the household's consumption, limited
    by what the roof can hold, then costed, and its bill savings and
    payback are estimated under the BERC slab tariff.
    """

    if monthly_bill_bdt <= 0:
        raise ValueError("Monthly bill must be greater than zero.")

    if roof_area_sqm <= 0:
        raise ValueError("Roof area must be greater than zero.")

    if not location or not location.strip():
        raise ValueError("Location is required.")

    bill = estimate_monthly_consumption(monthly_bill_bdt)
    monthly_consumption_kwh = bill["monthly_consumption_kwh"]

    place = get_location_yield(location)
    yearly_yield_per_kw = place["yearly_kwh_per_kw"]

    sizing = size_solar_system(
        roof_area_sqm=roof_area_sqm,
        monthly_consumption_kwh=monthly_consumption_kwh,
        yearly_yield_kwh_per_kw=yearly_yield_per_kw,
        target_offset_fraction=target_offset_fraction,
    )

    solar_capacity_kw = sizing["recommended_capacity_kw"]

    estimated_annual_kwh = yearly_yield_per_kw * solar_capacity_kw

    generation = {
        "capacity_kw": solar_capacity_kw,
        "yearly_yield_kwh_per_kw": round(yearly_yield_per_kw, 2),
        "daily_generation_kwh": round(estimated_annual_kwh / 365, 2),
        "monthly_generation_kwh": round(estimated_annual_kwh / 12, 2),
        "yearly_generation_kwh": round(estimated_annual_kwh, 2),
        "data_source": place["data_source"],
        "is_estimate": True,
    }

    monthly_generation_kwh = estimated_annual_kwh / 12

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

    battery = None

    if needs_battery:
        battery = calculate_battery_size(
            load_kw=backup_load_kw,
            backup_hours=backup_hours,
        )

    battery_capacity_kwh = battery["battery_capacity_kwh"] if battery else 0

    cost = estimate_solar_cost(
        capacity_kw=solar_capacity_kw,
        battery_capacity_kwh=battery_capacity_kwh,
    )

    savings = calculate_savings_and_payback(
        monthly_consumption_kwh=monthly_consumption_kwh,
        monthly_generation_kwh=monthly_generation_kwh,
        solar_cost_bdt=cost["solar_cost_bdt"],
        battery_cost_bdt=cost["battery_cost_bdt"],
    )

    limitations = [
        "Solar generation is estimated using PVGIS data "
        "for the resolved coordinates.",
        "Annual generation divided by 12 is an average, "
        "not a month-specific forecast.",
        "Roof shading, orientation, tilt, and structural "
        "suitability have not been inspected.",
        "Electricity consumption is estimated by inverting the BERC "
        "residential slab tariff; demand charges and other fees "
        "are not included.",
        "Equipment costs are illustrative, not verified "
        "current quotations.",
        "Actual output depends on installation and "
        "weather conditions.",
        "Roof capacity assumes about 5.5 m² per kW of panels "
        "and 70% usable roof area.",
        "Savings assume exported surplus has no cash value; only "
        "generation up to monthly consumption reduces the bill.",
        "Savings use average monthly figures; seasonal variation "
        "in consumption and generation is not modelled.",
        "Payback ignores tariff changes, panel degradation, "
        "maintenance, financing, and battery replacement.",
    ]

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
        "limitations": limitations,
    }
