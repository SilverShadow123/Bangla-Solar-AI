from typing import TypedDict


class SolarAgentState(TypedDict):
    messages: list
    user_location: str
    monthly_bill: float
    roof_area: float
    needs_battery: bool
    result: dict