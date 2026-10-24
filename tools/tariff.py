"""Bangladesh residential electricity tariff.

Rates follow the BERC order effective from the June 2026 billing cycle
(after BERC restored the 0-50 and 0-75 unit slabs to their earlier rates).
Update the constants below whenever BERC publishes a new order.
"""

TARIFF_BASIS = "BERC residential slab tariff, June 2026"

LIFELINE_LIMIT_KWH = 50
LIFELINE_RATE_BDT = 4.63

RESIDENTIAL_SLABS = [
    (75, 5.26),
    (200, 8.50),
    (300, 9.10),
    (400, 9.62),
    (600, 15.01),
    (None, 17.35),
]

VAT_RATE = 0.05
DEMAND_CHARGE_BDT = 0.0


def energy_charge(monthly_kwh: float) -> float:
    """Energy charge in BDT for a month's consumption (before VAT)."""

    if monthly_kwh < 0:
        raise ValueError("Consumption cannot be negative.")

    if monthly_kwh == 0:
        return 0.0

    if monthly_kwh <= LIFELINE_LIMIT_KWH:
        return monthly_kwh * LIFELINE_RATE_BDT

    charge = 0.0
    lower = 0.0

    for upper, rate in RESIDENTIAL_SLABS:
        top = monthly_kwh if upper is None else min(monthly_kwh, upper)

        if top > lower:
            charge += (top - lower) * rate

        if upper is None or monthly_kwh <= upper:
            break

        lower = upper

    return charge


def bill_for_kwh(
    monthly_kwh: float,
    vat_rate: float = VAT_RATE,
    demand_charge_bdt: float = DEMAND_CHARGE_BDT,
) -> float:
    """Total monthly bill in BDT for the given consumption."""

    return (
        energy_charge(monthly_kwh) + demand_charge_bdt
    ) * (1 + vat_rate)


def calculate_bill(monthly_kwh: float) -> dict:
    """Bill with a breakdown, for use as an agent tool."""

    energy = energy_charge(monthly_kwh)
    total = bill_for_kwh(monthly_kwh)

    return {
        "monthly_consumption_kwh": round(monthly_kwh, 2),
        "energy_charge_bdt": round(energy, 2),
        "demand_charge_bdt": DEMAND_CHARGE_BDT,
        "vat_rate": VAT_RATE,
        "total_bill_bdt": round(total, 2),
        "effective_rate_bdt_per_kwh": (
            round(total / monthly_kwh, 2) if monthly_kwh > 0 else None
        ),
        "tariff_basis": TARIFF_BASIS,
        "is_estimate": True,
    }


def kwh_from_bill(monthly_bill_bdt: float) -> float:
    """Invert the tariff: find the consumption that produces this bill.

    The bill is non-decreasing in consumption, so bisection is exact
    enough. If the bill is no more than the fixed charges, the
    consumption is zero.
    """

    if monthly_bill_bdt < 0:
        raise ValueError("Monthly bill cannot be negative.")

    if monthly_bill_bdt <= bill_for_kwh(0):
        return 0.0

    low = 0.0
    high = 100.0

    while bill_for_kwh(high) < monthly_bill_bdt:
        high *= 2

        if high > 1_000_000:
            raise ValueError("Monthly bill is unrealistically large.")

    for _ in range(80):
        mid = (low + high) / 2

        if bill_for_kwh(mid) < monthly_bill_bdt:
            low = mid
        else:
            high = mid

    return high
