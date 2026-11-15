"""
Domain-specific API Exception hierarchy for REST client operations.

Implements Production SDK Standard: non-2xx responses raise typed exceptions
that encapsulate status codes, raw responses, and parsed Pydantic error models.
"""

import requests
from pydantic import ValidationError

from framework.api.models import AuthError, Error


class ApiException(Exception):
    """Base exception for all API client errors."""

    def __init__(
        self,
        message: str,
        status_code: int,
        response: requests.Response,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class ApiValidationError(ApiException):
    """
    Raised when the server returns 400 (Bad Request) or 422 (Unprocessable Entity).
    Encapsulates the parsed OpenAPI Error model.
    """

    def __init__(self, status_code: int, response: requests.Response):
        try:
            self.error: Error = Error.model_validate(response.json())
            msg = f"HTTP {status_code} Validation Error: [{self.error.error}] {self.error.message}"
        except (ValueError, TypeError, ValidationError):
            self.error = Error(error="malformed_error_response", message=response.text)
            msg = f"HTTP {status_code} Validation Error: {response.text}"

        super().__init__(msg, status_code, response)


class ApiAuthError(ApiException):
    """
    Raised when the server returns 401 (Unauthorized) or 403 (Forbidden).
    Encapsulates the parsed OpenAPI AuthError model.
    """

    def __init__(self, status_code: int, response: requests.Response):
        try:
            self.auth_error: AuthError = AuthError.model_validate(response.json())
            msg = f"HTTP {status_code} Auth Error: [{self.auth_error.error}]"
        except (ValueError, TypeError, ValidationError):
            self.auth_error = AuthError(error="missing_user_id")
            msg = f"HTTP {status_code} Auth Error: {response.text}"

        super().__init__(msg, status_code, response)


class ApiHttpError(ApiException):
    """Raised for unexpected 4xx or 5xx server errors without domain error models."""

    def __init__(self, status_code: int, response: requests.Response):
        super().__init__(
            f"HTTP {status_code} Unexpected Error: {response.text}",
            status_code,
            response,
        )


def raise_api_error(response: requests.Response) -> None:
    """
    Inspect HTTP response status and raise typed domain exception for non-2xx responses.
    """
    if 200 <= response.status_code < 300:
        return

    status = response.status_code
    if status in (400, 422):
        raise ApiValidationError(status, response)
    if status in (401, 403):
        raise ApiAuthError(status, response)
    raise ApiHttpError(status, response)
