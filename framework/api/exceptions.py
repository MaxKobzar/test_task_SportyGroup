"""
Domain-specific API Exception hierarchy for REST client operations.

Implements Production SDK Standard: non-2xx responses raise typed exceptions
that encapsulate status codes, raw responses, and parsed Pydantic error models.
Follows DRY and KISS principles with a single unified constructor.
"""

from typing import Dict, Optional, Type, Union

import requests
from pydantic import BaseModel, ValidationError

from framework.api.models import (
    AuthError,
    Error,
    Error400,
    Error401,
    Error405,
    Error409,
    Error422,
    Error500,
)


class ApiException(Exception):
    """Base exception for all API client errors with a unified constructor."""

    title: str = "Unexpected Error"
    default_code: Optional[str] = None
    model_cls: Optional[Type[BaseModel]] = None
    strict_model_cls: Optional[Type[BaseModel]] = None

    def __init__(
        self,
        status_code: Union[int, str, requests.Response],
        response: Optional[Union[requests.Response, int]] = None,
        message: Optional[Union[requests.Response, str]] = None,
    ):
        # Resolve polymorphic arguments: (status_code, response), (response), or legacy (message, status_code, response)
        if isinstance(status_code, str):
            custom_msg: Optional[str] = status_code
            status = (
                int(response)
                if isinstance(response, (int, float))
                else getattr(message, "status_code", 0)
            )
            resp = message if not isinstance(message, str) else None
        elif isinstance(status_code, (int, float)):
            status = int(status_code)
            resp = response if not isinstance(response, (int, float)) else None
            custom_msg = message if isinstance(message, str) else None
        else:
            resp = status_code
            status = getattr(resp, "status_code", 0)
            custom_msg = message if isinstance(message, str) else None

        self.status_code: int = status
        self.response: Optional[requests.Response] = resp

        # Parse JSON payload safely
        raw_text = getattr(resp, "text", "") or ""
        json_data = None
        if resp is not None and hasattr(resp, "json") and callable(resp.json):
            try:
                json_data = resp.json()
            except (ValueError, TypeError):
                json_data = None

        # Validate domain error model or fall back to default error representation
        parsed_model = None
        if self.model_cls and json_data is not None:
            try:
                parsed_model = self.model_cls.model_validate(json_data)
            except (ValidationError, TypeError, ValueError):
                parsed_model = None

        if parsed_model is not None:
            err_code = getattr(parsed_model, "error", "")
            err_msg = getattr(parsed_model, "message", None)
            detail = f"[{err_code}] {err_msg}" if err_msg else f"[{err_code}]"
            default_msg = f"HTTP {status} {self.title}: {detail}"
        else:
            default_msg = f"HTTP {status} {self.title}: {raw_text}"
            if self.model_cls is not None:
                if self.model_cls is AuthError:
                    parsed_model = AuthError(error="missing_user_id")
                else:
                    parsed_model = Error(
                        error=self.default_code or "malformed_error_response",
                        message=raw_text,
                    )

        self.error: Optional[Error] = None
        self.auth_error: Optional[AuthError] = None

        if isinstance(parsed_model, AuthError):
            self.auth_error = parsed_model
        elif isinstance(parsed_model, Error):
            self.error = parsed_model

        # Validate strict OpenAPI example model if configured
        self.strict_model: Optional[BaseModel] = None
        if self.strict_model_cls and json_data is not None:
            try:
                self.strict_model = self.strict_model_cls.model_validate(json_data)
            except ValidationError:
                self.strict_model = None

        final_msg = custom_msg or default_msg
        super().__init__(final_msg)
        self.message = final_msg

    @classmethod
    def from_response(cls, response: requests.Response) -> "ApiException":
        """Factory constructor to instantiate the matching typed exception for an HTTP response."""
        if cls is not ApiException:
            return cls(response.status_code, response)

        status_exception_map: Dict[int, Type[ApiException]] = {
            400: ApiBadRequestError,
            401: ApiAuthError,
            405: ApiMethodNotAllowedError,
            409: ApiConflictError,
            422: ApiUnprocessableEntityError,
        }

        status = response.status_code
        if status >= 500:
            return ApiInternalServerError(status, response)
        error_cls = status_exception_map.get(status, ApiHttpError)
        return error_cls(status, response)


class ApiValidationError(ApiException):
    """
    Raised when the server returns 400 (Bad Request) or 422 (Unprocessable Entity).
    Encapsulates the parsed OpenAPI Error model.
    """

    title = "Validation Error"
    default_code = "malformed_error_response"
    model_cls = Error


class ApiBadRequestError(ApiValidationError):
    """Raised when server returns 400 (Bad Request)."""

    strict_model_cls = Error400


class ApiAuthError(ApiException):
    """
    Raised when the server returns 401 (Unauthorized).
    Encapsulates the parsed OpenAPI AuthError model.
    """

    title = "Auth Error"
    default_code = "missing_user_id"
    model_cls = AuthError
    strict_model_cls = Error401


class ApiMethodNotAllowedError(ApiException):
    """Raised when server returns 405 (Method Not Allowed)."""

    title = "Method Not Allowed"
    default_code = "method_not_allowed"
    model_cls = Error
    strict_model_cls = Error405


class ApiConflictError(ApiException):
    """Raised when server returns 409 (Conflict - Bet already in progress)."""

    title = "Conflict"
    default_code = "conflict"
    model_cls = Error
    strict_model_cls = Error409


class ApiUnprocessableEntityError(ApiValidationError):
    """Raised when server returns 422 (Unprocessable Entity)."""

    strict_model_cls = Error422


class ApiInternalServerError(ApiException):
    """Raised when server returns 500 (Internal Server Error)."""

    title = "Internal Server Error"
    default_code = "internal_server_error"
    model_cls = Error
    strict_model_cls = Error500


class ApiHttpError(ApiException):
    """Raised for unexpected 4xx or 5xx server errors without domain error models."""

    title = "Unexpected Error"


def raise_api_error(response: requests.Response) -> None:
    """
    Inspect HTTP response status and raise typed domain exception for non-2xx responses.
    """
    if 200 <= response.status_code < 300:
        return
    raise ApiException.from_response(response)
