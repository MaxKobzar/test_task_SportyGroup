"""
API package exports.
"""

from framework.api.client import BaseClient, BettingApiClient
from framework.api.exceptions import (
    ApiAuthError,
    ApiBadRequestError,
    ApiConflictError,
    ApiContractViolationError,
    ApiException,
    ApiHttpError,
    ApiInternalServerError,
    ApiMethodNotAllowedError,
    ApiUnprocessableEntityError,
    ApiValidationError,
    raise_for_api_error,
)
from framework.api.models.models import (
    Balance,
    Match,
    Odds,
    PlaceBetRequest,
    PlaceBetResponse,
    ResetBalanceResponse,
    SelectionType,
)

__all__ = [
    "ApiAuthError",
    "ApiBadRequestError",
    "ApiConflictError",
    "ApiContractViolationError",
    "ApiException",
    "ApiHttpError",
    "ApiInternalServerError",
    "ApiMethodNotAllowedError",
    "ApiUnprocessableEntityError",
    "ApiValidationError",
    "Balance",
    "BaseClient",
    "BettingApiClient",
    "Match",
    "Odds",
    "PlaceBetRequest",
    "PlaceBetResponse",
    "ResetBalanceResponse",
    "SelectionType",
    "raise_for_api_error",
]
