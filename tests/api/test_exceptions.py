"""
Unit tests for API Exception hierarchy and single constructor behavior.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from framework.api.client import BaseClient
from framework.api.exceptions import (
    ApiAuthError,
    ApiBadRequestError,
    ApiConflictError,
    ApiException,
    ApiHttpError,
    ApiInternalServerError,
    ApiMethodNotAllowedError,
    ApiUnprocessableEntityError,
    ApiValidationError,
    validate_rest_error,
)
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


@pytest.fixture(autouse=True)
def reset_api_state():
    """No-op fixture to bypass remote reset-balance HTTP call for pure unit tests."""
    return


def _mock_response(status_code: int, json_data=None, text: str = "") -> requests.Response:
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status_code
    resp.text = text
    if json_data is not None:
        resp.json.return_value = json_data
    else:
        resp.json.side_effect = ValueError("No JSON")
    return resp


class TestApiExceptionConstructor:
    """Tests verifying the unified constructor adheres to DRY/KISS."""

    def test_class_hierarchy(self):
        assert issubclass(ApiValidationError, ApiException)
        assert issubclass(ApiBadRequestError, ApiValidationError)
        assert issubclass(ApiUnprocessableEntityError, ApiValidationError)
        assert issubclass(ApiAuthError, ApiException)
        assert issubclass(ApiMethodNotAllowedError, ApiException)
        assert issubclass(ApiConflictError, ApiException)
        assert issubclass(ApiInternalServerError, ApiException)
        assert issubclass(ApiHttpError, ApiException)
        assert issubclass(ApiException, Exception)

    def test_bad_request_error_construction(self):
        body = {"error": "invalid_request", "message": "Request body must be a JSON object."}
        resp = _mock_response(400, json_data=body, text=str(body))
        err = ApiBadRequestError(400, resp)

        assert err.status_code == 400
        assert err.response is resp
        assert isinstance(err.error, Error)
        assert err.error.error == "invalid_request"
        assert err.error.message == "Request body must be a JSON object."
        assert err.strict_model == Error400()
        assert (
            "HTTP 400 Validation Error: [invalid_request] Request body must be a JSON object."
            in str(err)
        )

    def test_auth_error_construction(self):
        body = {"error": "missing_user_id"}
        resp = _mock_response(401, json_data=body, text=str(body))
        err = ApiAuthError(401, resp)

        assert err.status_code == 401
        assert err.response is resp
        assert isinstance(err.auth_error, AuthError)
        assert err.auth_error.error == "missing_user_id"
        assert err.strict_model == Error401()
        assert "HTTP 401 Auth Error: [missing_user_id]" in str(err)

    def test_method_not_allowed_error_construction(self):
        body = {"error": "insufficient_balance", "message": "Insufficient balance"}
        resp = _mock_response(405, json_data=body, text=str(body))
        err = ApiMethodNotAllowedError(405, resp)

        assert err.status_code == 405
        assert err.error is not None
        assert err.error.error == "insufficient_balance"
        assert err.strict_model == Error405()
        assert "HTTP 405 Method Not Allowed" in str(err)

    def test_conflict_error_construction(self):
        body = {"error": "insufficient_balance", "message": "Insufficient balance"}
        resp = _mock_response(409, json_data=body, text=str(body))
        err = ApiConflictError(409, resp)

        assert err.status_code == 409
        assert err.error is not None
        assert err.error.error == "insufficient_balance"
        assert err.strict_model == Error409()
        assert "HTTP 409 Conflict" in str(err)

    def test_unprocessable_entity_error_construction(self):
        body = {"error": "invalid_match_id", "message": "Match id is invalid."}
        resp = _mock_response(422, json_data=body, text=str(body))
        err = ApiUnprocessableEntityError(422, resp)

        assert err.status_code == 422
        assert err.error is not None
        assert err.error.error == "invalid_match_id"
        assert err.strict_model == Error422()
        assert "HTTP 422 Validation Error" in str(err)

    def test_internal_server_error_construction(self):
        body = {"error": "insufficient_balance", "message": "Insufficient balance"}
        resp = _mock_response(500, json_data=body, text=str(body))
        err = ApiInternalServerError(500, resp)

        assert err.status_code == 500
        assert err.error is not None
        assert err.error.error == "insufficient_balance"
        assert err.strict_model == Error500()
        assert "HTTP 500 Internal Server Error" in str(err)

    def test_single_response_argument_constructor(self):
        body = {"error": "invalid_request", "message": "Request body must be a JSON object."}
        resp = _mock_response(400, json_data=body, text=str(body))
        err = ApiBadRequestError(resp)

        assert err.status_code == 400
        assert err.error is not None
        assert err.error.error == "invalid_request"
        assert err.strict_model == Error400()

    def test_legacy_message_first_signature(self):
        resp = _mock_response(500, text="Internal crash")
        err = ApiException("Manual error message", 500, resp)

        assert err.status_code == 500
        assert err.response is resp
        assert str(err) == "Manual error message"

    def test_fallback_when_json_is_malformed(self):
        resp = _mock_response(400, text="<!DOCTYPE html><html>500 Error</html>")
        err = ApiBadRequestError(400, resp)

        assert err.status_code == 400
        assert err.error is not None
        assert err.error.error == "malformed_error_response"
        assert err.error.message == "<!DOCTYPE html><html>500 Error</html>"
        assert err.strict_model is None
        assert "HTTP 400 Validation Error: <!DOCTYPE html><html>500 Error</html>" in str(err)

    def test_auth_error_fallback_when_json_is_malformed(self):
        resp = _mock_response(401, text="Unauthorized string")
        err = ApiAuthError(401, resp)

        assert err.status_code == 401
        assert err.auth_error is not None
        assert err.auth_error.error == "missing_user_id"
        assert err.strict_model is None
        assert "HTTP 401 Auth Error: Unauthorized string" in str(err)

    def test_internal_server_error_fallback(self):
        resp = _mock_response(503, text="Service Unavailable")
        err = ApiInternalServerError(503, resp)

        assert err.status_code == 503
        assert err.error is not None
        assert err.error.error == "internal_server_error"
        assert err.error.message == "Service Unavailable"
        assert err.strict_model is None


class TestRaiseApiError:
    """Tests for raise_api_error and ApiException.from_response factory."""

    def test_no_exception_for_2xx(self):
        resp = _mock_response(200, text="OK")
        validate_rest_error(resp)

        resp204 = _mock_response(204, text="")
        validate_rest_error(resp204)

    def test_raise_bad_request(self):
        resp = _mock_response(400, json_data={"error": "invalid_request", "message": "msg"})
        with pytest.raises(ApiBadRequestError) as exc_info:
            validate_rest_error(resp)
        assert exc_info.value.status_code == 400
        assert isinstance(exc_info.value, ApiValidationError)

    def test_raise_auth_error(self):
        resp = _mock_response(401, json_data={"error": "missing_user_id"})
        with pytest.raises(ApiAuthError) as exc_info:
            validate_rest_error(resp)
        assert exc_info.value.status_code == 401

    def test_raise_method_not_allowed(self):
        resp = _mock_response(405, json_data={"error": "method_not_allowed", "message": "msg"})
        with pytest.raises(ApiMethodNotAllowedError):
            validate_rest_error(resp)

    def test_raise_conflict(self):
        resp = _mock_response(409, json_data={"error": "conflict", "message": "msg"})
        with pytest.raises(ApiConflictError):
            validate_rest_error(resp)

    def test_raise_unprocessable_entity(self):
        resp = _mock_response(422, json_data={"error": "invalid_match", "message": "msg"})
        with pytest.raises(ApiUnprocessableEntityError) as exc_info:
            validate_rest_error(resp)
        assert isinstance(exc_info.value, ApiValidationError)

    def test_raise_5xx_internal_server_error(self):
        resp500 = _mock_response(500, json_data={"error": "err", "message": "msg"})
        with pytest.raises(ApiInternalServerError):
            validate_rest_error(resp500)

        resp502 = _mock_response(502, text="Bad Gateway")
        with pytest.raises(ApiInternalServerError):
            validate_rest_error(resp502)

    def test_raise_unexpected_http_error(self):
        resp404 = _mock_response(404, text="Not Found")
        with pytest.raises(ApiHttpError) as exc_info:
            validate_rest_error(resp404)
        assert exc_info.value.status_code == 404
        assert "HTTP 404 Unexpected Error: Not Found" in str(exc_info.value)


class TestRaiseApiErrorDecorator:
    """Tests verifying raise_api_error operates cleanly as a decorator."""

    def test_decorator_without_parentheses_success(self):
        @validate_rest_error
        def make_request():
            return _mock_response(200, text="OK")

        resp = make_request()
        assert resp.status_code == 200

    def test_decorator_without_parentheses_raises_bad_request(self):
        @validate_rest_error
        def make_request():
            return _mock_response(
                400, json_data={"error": "invalid_request", "message": "bad payload"}
            )

        with pytest.raises(ApiBadRequestError) as exc_info:
            make_request()
        assert exc_info.value.status_code == 400
        assert exc_info.value.error is not None
        assert exc_info.value.error.error == "invalid_request"

    def test_decorator_with_parentheses_success(self):
        @validate_rest_error()
        def make_request():
            return _mock_response(204, text="")

        resp = make_request()
        assert resp.status_code == 204

    def test_decorator_with_parentheses_raises_auth_error(self):
        @validate_rest_error()
        def make_request():
            return _mock_response(401, json_data={"error": "missing_user_id"})

        with pytest.raises(ApiAuthError) as exc_info:
            make_request()
        assert exc_info.value.status_code == 401
        assert exc_info.value.auth_error is not None
        assert exc_info.value.auth_error.error == "missing_user_id"

    def test_decorator_on_class_method(self):
        class DummyClient:
            @validate_rest_error
            def execute(self, code: int):
                return _mock_response(code, text="Result")

        client = DummyClient()
        res = client.execute(200)
        assert res.status_code == 200

        with pytest.raises(ApiInternalServerError) as exc_info:
            client.execute(500)
        assert exc_info.value.status_code == 500

    def test_decorator_preserves_function_metadata(self):
        @validate_rest_error
        def my_custom_api_call():
            """Docstring for custom API call."""
            return _mock_response(200)

        assert my_custom_api_call.__name__ == "my_custom_api_call"
        assert my_custom_api_call.__doc__ == "Docstring for custom API call."

    def test_decorator_passthrough_non_response(self):
        @validate_rest_error
        def non_http_func():
            return {"data": 123}

        assert non_http_func() == {"data": 123}

    def test_base_client_methods_use_decorator(self):
        client = BaseClient(base_url="https://example.com")

        mock_err_resp = _mock_response(
            400, json_data={"error": "invalid_request", "message": "msg"}
        )
        with patch.object(client.session, "get", return_value=mock_err_resp):
            with pytest.raises(ApiBadRequestError):
                client.get("/test")

        mock_ok_resp = _mock_response(200, text="OK")
        with patch.object(client.session, "post", return_value=mock_ok_resp):
            resp = client.post("/test", json={})
            assert resp.status_code == 200
