from langchain_core.tools import tool

from services.solar_engine import assess_solar_feasibility
from tools.battery_sizing import calculate_battery_size
from tools.bill_analysis import estimate_monthly_consumption
from tools.cost_estimation import estimate_solar_cost
from tools.pv_yield import get_location_yield
from tools.solar_economics import calculate_savings_and_payback
from tools.solar_resource import get_solar_resource
from tools.tariff import calculate_bill


def _safe(function, **kwargs) -> dict:
    """Run a calculation and return errors as data, so a failed lookup
    (for example a PVGIS timeout) does not abort the whole chat turn."""

    try:
        return function(**kwargs)
    except (ValueError, RuntimeError) as error:
        return {"error": str(error)}


@tool
def assess_solar_tool(
    location: str,
    monthly_bill_bdt: float,
    roof_area_sqm: float,
    needs_battery: bool = False,
    backup_load_kw: float = 0.5,
    backup_hours: float = 4.0,
    assumption_overrides: dict | None = None,
    net_metering: bool = True,
) -> dict:
    """Run the full rooftop solar feasibility assessment.

    Uses the same engine as the app's Assess button: sizes the system
    from roof area and consumption, estimates PVGIS-based generation,
    cost, monthly bill savings and payback. Call this when the user
    asks "what if" about a different bill, roof area, location or
    battery setting.

    assumption_overrides: optional dict replacing stored assumptions,
    such as the user's own installer quote. Allowed keys: battery.depth_of_discharge, battery.inverter_efficiency, costs.battery_cost_per_kwh_bdt, costs.solar_cost_per_kw_bdt, pvgis.system_loss_percent, roof.area_per_kw_sqm, roof.usable_fraction, sizing.target_offset_fraction, tariff.demand_charge_bdt, tariff.vat_rate.
    If the current assessment lists user overrides, pass the same ones.
    net_metering: whether the household will use net metering (credit
    and payment for surplus power). The result includes month-by-month
    generation, bills before and after solar, and payback.
    """

    return _safe(
        assess_solar_feasibility,
        monthly_bill_bdt=monthly_bill_bdt,
        roof_area_sqm=roof_area_sqm,
        location=location,
        needs_battery=needs_battery,
        backup_load_kw=backup_load_kw,
        backup_hours=backup_hours,
        overrides=assumption_overrides,
        use_net_metering=net_metering,
    )


def _generation_for_location(capacity_kw: float, location: str) -> dict:
    if capacity_kw <= 0:
        raise ValueError("Solar capacity must be greater than zero.")

    place = get_location_yield(location)
    yearly = place["yearly_kwh_per_kw"] * capacity_kw

    return {
        "location": place["location"],
        "capacity_kw": capacity_kw,
        "yearly_yield_kwh_per_kw": place["yearly_kwh_per_kw"],
        "daily_generation_kwh": round(yearly / 365, 2),
        "monthly_generation_kwh": round(yearly / 12, 2),
        "yearly_generation_kwh": round(yearly, 2),
        "data_source": place["data_source"],
        "is_estimate": True,
    }


@tool
def solar_generation_tool(capacity_kw: float, location: str) -> dict:
    """Estimate daily, monthly and yearly generation in kWh for a system
    of the given capacity at a location in Bangladesh, using PVGIS data
    (the same data as the main assessment)."""

    return _safe(
        _generation_for_location,
        capacity_kw=capacity_kw,
        location=location,
    )


@tool
def battery_sizing_tool(load_kw: float, backup_hours: float) -> dict:
    """Estimate the battery capacity needed for a load and backup duration."""

    return _safe(
        calculate_battery_size,
        load_kw=load_kw,
        backup_hours=backup_hours,
    )


@tool
def bill_analysis_tool(monthly_bill_bdt: float) -> dict:
    """Estimate monthly electricity consumption (kWh) from a monthly
    electricity bill in BDT, using the BERC residential slab tariff."""

    return _safe(
        estimate_monthly_consumption,
        monthly_bill_bdt=monthly_bill_bdt,
    )


@tool
def electricity_bill_tool(monthly_kwh: float) -> dict:
    """Calculate the monthly electricity bill in BDT for a given
    consumption in kWh, using the BERC residential slab tariff."""

    return _safe(calculate_bill, monthly_kwh=monthly_kwh)


@tool
def solar_cost_tool(
    capacity_kw: float,
    battery_capacity_kwh: float = 0.0,
) -> dict:
    """Estimate solar system and optional battery costs in BDT."""

    return _safe(
        estimate_solar_cost,
        capacity_kw=capacity_kw,
        battery_capacity_kwh=battery_capacity_kwh,
    )


@tool
def savings_payback_tool(
    monthly_consumption_kwh: float,
    monthly_generation_kwh: float,
    solar_cost_bdt: float,
    battery_cost_bdt: float = 0.0,
    net_metering: bool = True,
) -> dict:
    """Estimate bill savings and simple payback in years from average
    monthly consumption, average monthly solar generation and system
    cost, under the BERC residential slab tariff and net metering. For a
    full month-by-month answer use assess_solar_tool instead."""

    return _safe(
        calculate_savings_and_payback,
        monthly_consumption_kwh=monthly_consumption_kwh,
        monthly_generation_kwh=monthly_generation_kwh,
        solar_cost_bdt=solar_cost_bdt,
        battery_cost_bdt=battery_cost_bdt,
        net_metering=net_metering,
    )


@tool
def solar_resource_tool(latitude: float, longitude: float) -> dict:
    """Retrieve estimated solar generation per 1 kW for geographic
    coordinates using PVGIS."""

    return _safe(
        get_solar_resource,
        latitude=latitude,
        longitude=longitude,
    )


@tool
def location_solar_resource_tool(location: str) -> dict:
    """Find a location in Bangladesh and retrieve its estimated solar
    generation per 1 kW using PVGIS."""

    try:
        place = get_location_yield(location)
    except ValueError as error:
        return {"found": False, "location": location, "message": str(error)}
    except RuntimeError as error:
        return {"error": str(error)}

    return {
        "found": True,
        "location": place["location"],
        "latitude": place["latitude"],
        "longitude": place["longitude"],
        "solar_resource": place["solar_resource"],
    }


solar_tools = [
    assess_solar_tool,
    solar_generation_tool,
    battery_sizing_tool,
    bill_analysis_tool,
    electricity_bill_tool,
    solar_cost_tool,
    savings_payback_tool,
    solar_resource_tool,
    location_solar_resource_tool,
]
