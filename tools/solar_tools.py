
from langchain_core.tools import tool

from tools.solar_generation import calculate_solar_generation
from tools.battery_sizing import calculate_battery_size
from tools.bill_analysis import estimate_monthly_consumption
from tools.cost_estimation import estimate_solar_cost
from tools.solar_resource import get_solar_resource
from tools.location import get_location_coordinates



@tool
def solar_generation_tool(
    capacity_kw: float,
    peak_sun_hours: float = 4.5,
    system_efficiency: float = 0.80,
) -> dict:
    """Estimate daily and monthly solar generation in kWh.

    Args:
        capacity_kw: Solar system capacity in kW.
        peak_sun_hours: Average equivalent peak sun hours per day.
        system_efficiency: System efficiency as a decimal,
            such as 0.80 for 80% or 0.90 for 90%.
    """
    return calculate_solar_generation(
        capacity_kw=capacity_kw,
        peak_sun_hours=peak_sun_hours,
        system_efficiency=system_efficiency,
    )



@tool
def battery_sizing_tool(load_kw: float, backup_hours: float) -> dict:
    """Estimate the battery capacity needed for a load and backup duration."""
    return calculate_battery_size(
        load_kw=load_kw,
        backup_hours=backup_hours,
    )


@tool
def bill_analysis_tool(monthly_bill_bdt: float) -> dict:
    """Estimate monthly electricity consumption from a bill in BDT."""
    return estimate_monthly_consumption(
        monthly_bill_bdt=monthly_bill_bdt,
    )


@tool
def solar_cost_tool(
    capacity_kw: float,
    battery_capacity_kwh: float = 0.0,
) -> dict:
    """Estimate solar system and optional battery costs in BDT."""
    return estimate_solar_cost(
        capacity_kw=capacity_kw,
        battery_capacity_kwh=battery_capacity_kwh,
    )


@tool
def solar_resource_tool(latitude: float, longitude: float) -> dict:
    """Retrieve estimated solar generation for geographic coordinates using PVGIS."""
    return get_solar_resource(
        latitude=latitude,
        longitude=longitude,
    )


@tool
def location_solar_resource_tool(location: str) -> dict:
    """Find a location in Bangladesh and retrieve its estimated solar generation using PVGIS."""
    coordinates = get_location_coordinates(location)

    if not coordinates["found"]:
        return {
            "found": False,
            "location": location,
            "message": coordinates["message"],
        }

    solar_data = get_solar_resource(
        latitude=coordinates["latitude"],
        longitude=coordinates["longitude"],
    )

    return {
        "found": True,
        "location": coordinates["location"],
        "latitude": coordinates["latitude"],
        "longitude": coordinates["longitude"],
        "solar_resource": solar_data,
    }


solar_tools = [
    solar_generation_tool,
    battery_sizing_tool,
    bill_analysis_tool,
    solar_cost_tool,
    solar_resource_tool,
    location_solar_resource_tool,
]
