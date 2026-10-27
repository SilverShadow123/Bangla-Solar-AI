import requests

from tools.config import resolve_assumptions


def get_solar_resource(
    latitude: float,
    longitude: float,
    pvgis: dict | None = None,
) -> dict:
    """Fetch estimated PV performance for a geographic location.

    API URL, timeout, system loss and mounting angles come from the
    'pvgis' section of data/assumptions.json unless a settings dict is
    passed in.
    """

    if not -90 <= latitude <= 90:
        raise ValueError("Latitude must be between -90 and 90.")

    if not -180 <= longitude <= 180:
        raise ValueError("Longitude must be between -180 and 180.")

    settings = pvgis if pvgis is not None else resolve_assumptions()["pvgis"]

    params = {
        "lat": latitude,
        "lon": longitude,
        "peakpower": 1,
        "loss": settings["system_loss_percent"],
        "outputformat": "json",
    }

    # Mounting: send nothing (PVGIS defaults) unless configured.
    if settings["use_optimal_angles"]:
        params["optimalangles"] = 1
    else:
        if settings["angle_degrees"] is not None:
            params["angle"] = settings["angle_degrees"]

        if settings["aspect_degrees"] is not None:
            params["aspect"] = settings["aspect_degrees"]

    try:
        response = requests.get(
            settings["api_url"],
            params=params,
            timeout=settings["timeout_seconds"],
        )
        response.raise_for_status()
        data = response.json()

    except requests.RequestException as error:
        raise RuntimeError(
            f"Could not retrieve solar resource data: {error}"
        ) from error

    try:
        totals = data["outputs"]["totals"]["fixed"]

        yearly_energy = float(totals["E_y"])
        monthly_energy = yearly_energy / 12

    except (KeyError, TypeError, ValueError) as error:
        raise RuntimeError(
            "The solar API returned an unexpected response."
        ) from error

    # Month-by-month profile for 1 kW (January to December). If PVGIS
    # does not return it, callers fall back to a flat year.
    monthly_profile = None

    try:
        rows = sorted(
            data["outputs"]["monthly"]["fixed"],
            key=lambda row: row["month"],
        )
        values = [float(row["E_m"]) for row in rows]

        if len(values) == 12 and sum(values) > 0:
            # Scale so the months add up to the yearly total exactly.
            scale = yearly_energy / sum(values)
            monthly_profile = [round(v * scale, 2) for v in values]
    except (KeyError, TypeError, ValueError):
        monthly_profile = None

    return {
        "latitude": latitude,
        "longitude": longitude,
        "system_capacity_kw": 1.0,
        "estimated_yearly_generation_kwh": round(yearly_energy, 2),
        "estimated_monthly_generation_kwh": round(monthly_energy, 2),
        "monthly_generation_kwh_per_kw": monthly_profile,
        "system_loss_percent": settings["system_loss_percent"],
        "data_source": "European Commission PVGIS",
        "is_estimate": True,
    }
