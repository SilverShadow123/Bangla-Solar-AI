
from tools.solar_tools import (
    solar_generation_tool,
    battery_sizing_tool,
    bill_analysis_tool,
    solar_cost_tool,
)


def test_solar_generation_tool():
    result = solar_generation_tool.invoke({"capacity_kw": 3.5})
    assert result["monthly_generation_kwh"] > 0


def test_battery_sizing_tool():
    result = battery_sizing_tool.invoke({
        "load_kw": 0.5,
        "backup_hours": 4,
    })
    assert result["battery_capacity_kwh"] > 0


def test_bill_analysis_tool():
    result = bill_analysis_tool.invoke({"monthly_bill_bdt": 3000})
    assert result["monthly_consumption_kwh"] > 0


def test_solar_cost_tool():
    result = solar_cost_tool.invoke({"capacity_kw": 3.5})
    assert result["total_cost_bdt"] > 0
