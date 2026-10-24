"""Single source of truth for location-specific PV yield.

Both the assessment engine and the chat agent's tools call
get_location_yield(), so they always use the same PVGIS-based numbers.
Results are cached to avoid repeated Nominatim and PVGIS requests.
"""

from functools import lru_cache

from tools.location import get_location_coordinates
from tools.solar_resource import get_solar_resource


@lru_cache(maxsize=256)
def _cached_coordinates(location_key: str) -> dict:
    return get_location_coordinates(location_key)


@lru_cache(maxsize=256)
def _cached_resource(latitude: float, longitude: float) -> dict:
    return get_solar_resource(latitude=latitude, longitude=longitude)


def get_location_yield(location: str) -> dict:
    """Resolve a Bangladesh location and return its PVGIS yield per kW."""

    if not location or not location.strip():
        raise ValueError("Location is required.")

    key = " ".join(location.lower().split())
    coordinates = _cached_coordinates(key)

    if not coordinates["found"]:
        raise ValueError(f"Could not find the location: {location}")

    resource = dict(
        _cached_resource(
            round(coordinates["latitude"], 3),
            round(coordinates["longitude"], 3),
        )
    )

    return {
        "location": coordinates["location"],
        "latitude": coordinates["latitude"],
        "longitude": coordinates["longitude"],
        "yearly_kwh_per_kw": resource["estimated_yearly_generation_kwh"],
        "solar_resource": resource,
        "data_source": resource["data_source"],
    }
