
from tools.solar_generation import calculate_solar_generation
from tools.battery_sizing import calculate_battery_size
from tools.bill_analysis import estimate_monthly_consumption
from tools.cost_estimation import estimate_solar_cost
from tools.location import get_location_coordinates
from tools.solar_resource import get_solar_resource


def assess_solar_feasibility(
    monthly_bill_bdt: float,
    roof_area_sqm: float,
    location: str,
    needs_battery: bool = False,
    backup_load_kw: float = 0.5,
    backup_hours: float = 4.0,
) -> dict:
    """Create a preliminary, location-aware solar assessment."""

    if roof_area_sqm <= 0:
        raise ValueError("Roof area must be greater than zero.")

    if not location or not location.strip():
        raise ValueError("Location is required.")

    bill = estimate_monthly_consumption(monthly_bill_bdt)

    usable_roof_area = roof_area_sqm * 0.70
    solar_capacity_kw = usable_roof_area / 10

    coordinates = get_location_coordinates(location)

    if not coordinates["found"]:
        raise ValueError(
            f"Could not find the location: {location}"
        )

    solar_resource = get_solar_resource(
        latitude=coordinates["latitude"],
        longitude=coordinates["longitude"],
    )

    reference_annual_kwh = solar_resource[
        "estimated_yearly_generation_kwh"
    ]

    estimated_annual_kwh = (
        reference_annual_kwh * solar_capacity_kw
    )

    generation = {
        "capacity_kw": round(solar_capacity_kw, 2),
        "daily_generation_kwh": round(
            estimated_annual_kwh / 365, 2
        ),
        "monthly_generation_kwh": round(
            estimated_annual_kwh / 12, 2
        ),
        "yearly_generation_kwh": round(
            estimated_annual_kwh, 2
        ),
        "data_source": solar_resource["data_source"],
        "is_estimate": True,
    }

    monthly_generation_kwh = generation["monthly_generation_kwh"]
    monthly_consumption_kwh = bill["monthly_consumption_kwh"]

    energy_balance_kwh = round(
        monthly_generation_kwh - monthly_consumption_kwh,
        2,
    )

    if energy_balance_kwh > 0:
        energy_assessment = {
            "status": "potential_surplus",
            "monthly_surplus_kwh": energy_balance_kwh,
            "message": (
                "Estimated solar generation exceeds "
                "estimated household consumption."
            ),
        }
    elif energy_balance_kwh < 0:
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
            "monthly_difference_kwh": 0.0,
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

    battery_capacity_kwh = (
        battery["battery_capacity_kwh"]
        if battery
        else 0
    )

    cost = estimate_solar_cost(
        capacity_kw=solar_capacity_kw,
        battery_capacity_kwh=battery_capacity_kwh,
    )

    return {
        "location": coordinates["location"],
        "latitude": coordinates["latitude"],
        "longitude": coordinates["longitude"],
        "energy_assessment": energy_assessment,
        "roof_area_sqm": roof_area_sqm,
        "usable_roof_area_sqm": round(
            usable_roof_area, 2
        ),
        "solar_capacity_kw": round(
            solar_capacity_kw, 2
        ),
        "electricity": bill,
        "generation": generation,
        "solar_resource": solar_resource,
        "battery": battery,
        "cost": cost,
        "limitations": [
            "Solar generation is estimated using PVGIS data "
            "for the resolved coordinates.",
            "Annual generation divided by 12 is an average, "
            "not a month-specific forecast.",
            "Roof shading, orientation, tilt, and structural "
            "suitability have not been inspected.",
            "Electricity consumption is estimated using an "
            "assumed rate, not the actual tariff calculation.",
            "Equipment costs are illustrative, not verified "
            "current quotations.",
            "Actual output depends on installation and "
            "weather conditions.",
        ],
    }
