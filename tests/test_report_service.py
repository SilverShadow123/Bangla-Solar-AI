
from unittest.mock import patch

from services.solar_engine import assess_solar_feasibility
from services.report_service import generate_solar_report


def make_assessment(location="Barishal, Bangladesh"):
    coordinates = {
        "found": True,
        "location": location,
        "latitude": 22.49,
        "longitude": 90.35,
    }

    solar_resource = {
        "latitude": 22.49,
        "longitude": 90.35,
        "system_capacity_kw": 1.0,
        "estimated_yearly_generation_kwh": 1294.01,
        "estimated_monthly_generation_kwh": 107.83,
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
            needs_battery=True,
        )


def test_solar_report_english():
    result = make_assessment()
    report = generate_solar_report(result, language="en")

    assert "Solar Feasibility Report" in report
    assert "Barishal, Bangladesh" in report
    assert "Estimated total cost" in report
    assert "377.42 kWh" in report
    assert "Estimated battery capacity" in report


def test_solar_report_bangla():
    result = make_assessment(location="বরিশাল, বাংলাদেশ")
    report = generate_solar_report(result, language="bn")

    assert "বাংলা সোলার AI" in report
    assert "বরিশাল" in report
    assert "সীমাবদ্ধতা" in report


def test_solar_report_without_battery():
    coordinates = {
        "found": True,
        "location": "Barishal, Bangladesh",
        "latitude": 22.49,
        "longitude": 90.35,
    }

    solar_resource = {
        "latitude": 22.49,
        "longitude": 90.35,
        "system_capacity_kw": 1.0,
        "estimated_yearly_generation_kwh": 1294.01,
        "estimated_monthly_generation_kwh": 107.83,
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
        result = assess_solar_feasibility(
            monthly_bill_bdt=3000,
            roof_area_sqm=50,
            location="Barishal, Bangladesh",
            needs_battery=False,
        )

    report = generate_solar_report(result, language="en")

    assert "Solar Feasibility Report" in report
    assert "Estimated battery capacity" not in report
