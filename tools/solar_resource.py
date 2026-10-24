
import requests


def get_solar_resource(latitude: float, longitude: float) -> dict:
    """Fetch estimated PV performance for a geographic location."""

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90.")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180.")

    url = (
        "https://re.jrc.ec.europa.eu/api/v5_3/PVcalc"
    )

    params = {
        "lat": latitude,
        "lon": longitude,
        "peakpower": 1,
        "loss": 14,
        "outputformat": "json",
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

    except requests.RequestException as error:
        raise RuntimeError(
            f"Could not retrieve solar resource data: {error}"
        ) from error

    try:
        outputs = data["outputs"]
        totals = outputs["totals"]["fixed"]

        yearly_energy = float(totals["E_y"])
        monthly_energy = yearly_energy / 12

    except (KeyError, TypeError, ValueError) as error:
        raise RuntimeError(
            "The solar API returned an unexpected response."
        ) from error

    return {
        "latitude": latitude,
        "longitude": longitude,
        "system_capacity_kw": 1.0,
        "estimated_yearly_generation_kwh": round(
            yearly_energy, 2
        ),
        "estimated_monthly_generation_kwh": round(
            monthly_energy, 2
        ),
        "data_source": "European Commission PVGIS",
        "is_estimate": True,
    }
