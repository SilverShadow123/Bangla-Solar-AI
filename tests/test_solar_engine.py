
from unittest.mock import patch

from services.solar_engine import assess_solar_feasibility



def run_assessment_with_generation(monthly_generation_kwh: float):
    coordinates = {
        "found": True,
        "location": "Barishal, Bangladesh",
        "latitude": 22.49,
        "longitude": 90.35,
    }

    # A 50 m² roof produces an estimated 3.5 kW system.
    # The engine multiplies PVGIS's 1 kW annual yield
    # by this capacity, so divide by 3.5 here.
    annual_generation_for_1kw = (
        monthly_generation_kwh * 12 / 3.5
    )

    solar_resource = {
        "latitude": 22.49,
        "longitude": 90.35,
        "system_capacity_kw": 1.0,
        "estimated_yearly_generation_kwh": (
            annual_generation_for_1kw
        ),
        "estimated_monthly_generation_kwh": (
            annual_generation_for_1kw / 12
        ),
        "data_source": "European Commission PVGIS",
        "is_estimate": True,
    }

    with (
        patch(
            "services.solar_engine.get_location_coordinates",
            return_value=coordinates,
        ),
        patch(
            "services.solar_engine.get_solar_resource",
            return_value=solar_resource,
        ),
    ):
        return assess_solar_feasibility(
            monthly_bill_bdt=3000,
            roof_area_sqm=50,
            location="Barishal, Bangladesh",
        )



def test_energy_assessment_surplus():
    result = run_assessment_with_generation(1500)

    assert (
        result["energy_assessment"]["status"]
        == "potential_surplus"
    )
    assert (
        result["energy_assessment"]["monthly_surplus_kwh"]
        > 0
    )


def test_energy_assessment_shortfall():
    result = run_assessment_with_generation(100)

    assert (
        result["energy_assessment"]["status"]
        == "potential_shortfall"
    )
    assert (
        result["energy_assessment"]["monthly_shortfall_kwh"]
        > 0
    )


def test_energy_assessment_balanced():
    result = run_assessment_with_generation(300)

    assert (
        result["energy_assessment"]["status"]
        == "approximately_balanced"
    )
    assert (
        result["energy_assessment"]["monthly_difference_kwh"]
        == 0.0
    )
