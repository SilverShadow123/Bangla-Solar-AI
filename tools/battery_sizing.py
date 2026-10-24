
def calculate_battery_size(
    load_kw: float,
    backup_hours: float,
    depth_of_discharge: float = 0.80,
    inverter_efficiency: float = 0.90,
) -> dict:

    if load_kw <= 0:
        raise ValueError("Load must be greater than zero.")

    if backup_hours <= 0:
        raise ValueError("Backup hours must be greater than zero.")

    if not 0 < depth_of_discharge <= 1:
        raise ValueError("Depth of discharge must be between 0 and 1.")

    if not 0 < inverter_efficiency <= 1:
        raise ValueError("Inverter efficiency must be between 0 and 1.")

    required_energy = load_kw * backup_hours

    battery_capacity = required_energy / (
        depth_of_discharge * inverter_efficiency
    )

    return {
        "load_kw": load_kw,
        "backup_hours": backup_hours,
        "required_energy_kwh": round(required_energy, 2),
        "battery_capacity_kwh": round(battery_capacity, 2),
        "is_estimate": True,
    }
