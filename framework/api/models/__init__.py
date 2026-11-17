"""
Pydantic contract models of the Betting API: domain request/response models and error bodies.
"""

from framework.api.models.betting import (
    Balance,
    Match,
    Odds,
    PlaceBetRequest,
    PlaceBetResponse,
    ResetBalanceResponse,
    SelectionType,
)
from framework.api.models.errors import (
    AuthError,
    Error,
    Error400,
    Error401,
    Error405,
    Error409,
    Error422,
    Error500,
)

__all__ = [
    "AuthError",
    "Balance",
    "Error",
    "Error400",
    "Error401",
    "Error405",
    "Error409",
    "Error422",
    "Error500",
    "Match",
    "Odds",
    "PlaceBetRequest",
    "PlaceBetResponse",
    "ResetBalanceResponse",
    "SelectionType",
]
