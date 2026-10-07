from decimal import ROUND_HALF_UP, Decimal

ZERO = Decimal("0.00")
_CENT = Decimal("0.01")


def money(value) -> Decimal:
    return Decimal(value).quantize(_CENT, rounding=ROUND_HALF_UP)


def percent(part: Decimal, whole: Decimal) -> Decimal:
    if not whole:
        return ZERO
    return money(part / whole * 100)
