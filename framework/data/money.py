"""
Money arithmetic, formatting and parsing of numbers shown in the UI.

Currency is Decimal and rounds half-up to cents, the way the UI displays it. round() on a
float operates on its binary approximation and breaks ties to even (round(2.675, 2) == 2.67),
so expected values computed that way are off by a cent often enough to fail a correct UI.

Every regex that reads a number out of UI text lives here, so the page objects share one
definition of what an amount looks like.
"""

import re
from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")

_NUMBER = re.compile(r"[-+]?\d+(?:\.\d+)?")
_EUR_AMOUNT = re.compile(r"€\s*[-+]?\d")


def to_cents(amount: Decimal) -> Decimal:
    """Round an amount half-up to two decimal places."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def format_eur(amount: Decimal) -> str:
    """Render an amount the way the UI shows currency (spec §3: EUR, 2 decimals)."""
    return f"€{to_cents(amount)}"


def contains_eur_amount(text: str) -> bool:
    """True if text shows a euro amount, e.g. 'Balance: €120.00' (not a loading placeholder)."""
    return _EUR_AMOUNT.search(text) is not None


def find_number(text: str) -> str | None:
    """First signed decimal number in text as written, thousands separators removed."""
    match = _NUMBER.search(text.replace(",", ""))
    return match.group() if match else None


def parse_amount(text: str) -> Decimal:
    """Extract the first signed decimal number from UI text such as 'Balance: €1,120.50'."""
    number = find_number(text)
    if number is None:
        raise ValueError(f"No numeric amount in {text!r}")
    return Decimal(number)
