"""
Typed API exception hierarchy.

Every non-2xx response raises the ApiException subclass mapped to its status code, with its
error body validated against that status's model from framework.api.models
(Error400, Error401, Error405, Error409, Error422, Error500).

A documented status whose body breaks its model (missing or empty field, wrong type,
undocumented field, code or message, non-JSON body) raises ApiContractViolationError. So does a 2xx
body that breaks its response model (see parse_model, used by the client).
Undocumented statuses (e.g. a 502 from a proxy) raise ApiHttpError with no body contract.

Exceptions are plain data holders: the from_response factory does all parsing, so an
exception can never be created half-initialised.
"""

from collections.abc import Callable
from functools import wraps
from typing import ClassVar, ParamSpec, TypeVar

import requests
from pydantic import BaseModel, ValidationError

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

P = ParamSpec("P")
TModel = TypeVar("TModel", bound=BaseModel)

ErrorBody = Error | AuthError


class ApiContractViolationError(Exception):
    """A response body breaks its documented model: a product defect, not a client error."""

    def __init__(self, response: requests.Response, cause: ValidationError):
        self.response = response
        self.status_code = response.status_code
        self.validation_error = cause
        request = response.request
        violations = "; ".join(
            f"{'.'.join(map(str, err['loc'])) or '<body>'}={err.get('input')!r}: {err['msg']}"
            for err in cause.errors()
        )
        super().__init__(
            f"{request.method} {request.path_url} [{self.status_code}] broke the "
            f"{cause.title} contract: {violations}"
        )


def parse_model(model: type[TModel], data: object, response: requests.Response) -> TModel:
    """Validate decoded data against model; a violation raises ApiContractViolationError."""
    try:
        return model.model_validate(data)
    except ValidationError as error:
        raise ApiContractViolationError(response, error) from error


def parse_json_model(model: type[TModel], response: requests.Response) -> TModel:
    """Validate the raw JSON body against model; invalid JSON is a violation too."""
    try:
        return model.model_validate_json(response.content)
    except ValidationError as error:
        raise ApiContractViolationError(response, error) from error


class ApiException(Exception):
    """Base exception for non-2xx API responses. Build it with from_response."""

    title: ClassVar[str] = "Unexpected Error"
    error_model: ClassVar[type[ErrorBody] | None] = None

    def __init__(self, response: requests.Response, error: ErrorBody | None = None):
        self.response = response
        self.status_code = response.status_code
        self.error = error
        super().__init__(f"HTTP {self.status_code} {self.title}: {self._detail()}")

    def _detail(self) -> str:
        if isinstance(self.error, Error) and self.error.message:
            return f"[{self.error.error}] {self.error.message}"
        if self.error is not None:
            return f"[{self.error.error}]"
        return self.response.text

    @classmethod
    def from_response(cls, response: requests.Response) -> "ApiException":
        """
        Typed exception for a non-2xx response, with its error body validated.

        Raises ApiContractViolationError when a documented status returns a body that
        breaks its schema model.
        """
        exception_cls = _STATUS_EXCEPTIONS.get(response.status_code, ApiHttpError)
        if exception_cls.error_model is None:
            return exception_cls(response)
        error = parse_json_model(exception_cls.error_model, response)
        return exception_cls(response, error)


class ApiValidationError(ApiException):
    """400 / 422: the request was rejected by validation."""

    title = "Validation Error"


class ApiBadRequestError(ApiValidationError):
    """400 Bad Request: malformed or non-object JSON payload."""

    error_model = Error400


class ApiUnprocessableEntityError(ApiValidationError):
    """422 Unprocessable Entity: semantic validation failure (selection, stake, match)."""

    error_model = Error422


class ApiAuthError(ApiException):
    """401 Unauthorized: missing or invalid x-user-id."""

    title = "Auth Error"
    error_model = Error401


class ApiMethodNotAllowedError(ApiException):
    """405: the test suite expects this status for insufficient balance."""

    title = "Method Not Allowed"
    error_model = Error405


class ApiConflictError(ApiException):
    """409 Conflict: a bet is already being processed for this user."""

    title = "Conflict"
    error_model = Error409


class ApiInternalServerError(ApiException):
    """500 Internal Server Error (documented, so its body must match the Error schema)."""

    title = "Internal Server Error"
    error_model = Error500


class ApiHttpError(ApiException):
    """Any undocumented non-2xx status (e.g. a 502 from a proxy): no body contract."""


_STATUS_EXCEPTIONS: dict[int, type[ApiException]] = {
    400: ApiBadRequestError,
    401: ApiAuthError,
    405: ApiMethodNotAllowedError,
    409: ApiConflictError,
    422: ApiUnprocessableEntityError,
    500: ApiInternalServerError,
}
"""Documented status codes mapped to their typed exception; anything else is ApiHttpError."""


def raise_for_api_error(
    send: Callable[P, requests.Response],
) -> Callable[P, requests.Response]:
    """Decorator: raise the typed ApiException for any non-2xx response."""

    @wraps(send)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> requests.Response:
        response = send(*args, **kwargs)
        if not 200 <= response.status_code < 300:
            raise ApiException.from_response(response)
        return response

    return wrapper
