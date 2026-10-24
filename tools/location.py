
import requests


def get_location_coordinates(location: str) -> dict:
    """Find a location in Bangladesh and return its coordinates."""

    if not location or not location.strip():
        raise ValueError("Please enter a location.")

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": location.strip(),
        "countrycodes": "bd",
        "format": "jsonv2",
        "limit": 1,
        "addressdetails": 1,
    }

    headers = {
        "User-Agent": "BanglaSolarAI/0.1 (contact: hasanmohasin852@gmail.com)"
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=15,
        )
        response.raise_for_status()
        results = response.json()

    except requests.RequestException as error:
        raise RuntimeError(
            f"Geocoding service request failed: {error}"
        ) from error

    if not results:
        return {
            "found": False,
            "message": "Location not found in Bangladesh.",
        }

    result = results[0]

    return {
        "found": True,
        "location": result["display_name"],
        "latitude": float(result["lat"]),
        "longitude": float(result["lon"]),
    }
