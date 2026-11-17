"""
Money arithmetic and formatting.

Currency is Decimal and rounds half-up to cents, the way the UI displays it. round() on a
float operates on its binary approximation and breaks ties to even (round(2.675, 2) == 2.67),
so expected values computed that way are off by a cent often enough to fail a correct UI.
"""

import re
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


def to_cents(amount: Decimal) -> Decimal:
    """Round an amount half-up to two decimal places."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def format_eur(amount: Decimal) -> str:
    """Render an amount the way the UI shows currency (spec §3: EUR, 2 decimals)."""
    return f"€{to_cents(amount)}"


def parse_amount(text: str) -> Decimal:
    """Extract the first signed decimal number from UI text such as 'Balance: €1,120.50'."""
    match = re.search(r"[-+]?\d+(?:\.\d+)?", text.replace(",", ""))
    if match is None:
        raise ValueError(f"No numeric amount in {text!r}")
    return Decimal(match.group())
