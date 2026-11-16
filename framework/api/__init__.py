"""
API package exports.
"""

from framework.api.client import BaseClient, BettingApiClient
from framework.api.exceptions import (
    ApiAuthError,
    ApiException,
    ApiHttpError,
    ApiValidationError,
    validate_rest_error,
)
from framework.api.models import (
    AuthError,
    Balance,
    Error,
    Match,
    Odds,
    PlaceBetRequest,
    PlaceBetResponse,
    ResetBalanceResponse,
    SelectionType,
)

__all__ = [
    "BaseClient",
    "BettingApiClient",
    "ApiException",
    "ApiValidationError",
    "ApiAuthError",
    "ApiHttpError",
    "validate_rest_error",
    "AuthError",
    "Balance",
    "Error",
    "Match",
    "Odds",
    "PlaceBetRequest",
    "PlaceBetResponse",
    "ResetBalanceResponse",
    "SelectionType",
]
