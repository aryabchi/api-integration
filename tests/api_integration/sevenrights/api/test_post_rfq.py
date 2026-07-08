import json
from unittest.mock import MagicMock, patch

import pytest
import requests

from api_integration.sevenrights.api.post_rfq import post_rfq
from api_integration.sevenrights.api.schemas.api_requests import RfqCreateRequest


@pytest.fixture
def fake_settings():
    settings = MagicMock()
    settings.SEVEN_RIGHTS_API_URL = "https://lk.7rights.ru/api/v1"
    settings.SEVEN_RIGHTS_API_KEY = "test-key"
    settings.SEVEN_RIGHTS_API_AWAIT_TIMEOUT = 30
    return settings


@pytest.fixture
def payload():
    return {
        "title": "test",
        "finish_datetime": "2026-08-01T17:00:00",
        "requirements": "req",
        "contract_start_date": "2026-07-08",
        "contract_end_date": "2026-09-01",
        "is_invite_link_enabled": False,
        "transport_type_ids": [1],
        "participant_access_type": 0,
        "freight_spend_of_event": 1,
        "freight_spend_currency_id": 1,
        "type_view": 2,
        "traffic_light_type": 1,
        "show_best_price": False,
        "prolongacia": False,
        "is_ban_on_price_increases_on_this_tour": True,
        "traffic_light_price_type": 2,
        "price_green_finish_percent": 93,
        "price_yellow_finish_percent": 85,
    }


# Retries on connection/DNS error and returns informative error after exhaustion
def test_name_resolution_error_retries(fake_settings, payload):

    fake_model = MagicMock()
    fake_model.model_dump.return_value = {"title": "test"}

    def _fast_retry(**kwargs):
        kwargs["attempts"] = 3
        kwargs["multiplier"] = 2
        kwargs["min_wait"] = 0
        kwargs["max_wait"] = 0
        kwargs["exception_types"] = (requests.ConnectionError,)

        def decorator(func):
            import logging
            from tenacity import (
                retry,
                stop_after_attempt,
                wait_exponential,
                retry_if_exception_type,
                before_sleep_log,
            )

            _logger = logging.getLogger(func.__module__)
            _retry = retry(
                stop=stop_after_attempt(kwargs["attempts"]),
                wait=wait_exponential(
                    multiplier=kwargs["multiplier"],
                    min=kwargs["min_wait"],
                    max=kwargs["max_wait"],
                ),
                retry=retry_if_exception_type(kwargs["exception_types"]),
                before_sleep=before_sleep_log(_logger, logging.WARNING),
            )
            return _retry(func)

        return decorator

    with (
        patch(
            "api_integration.sevenrights.api.post_rfq.get_settings",
            return_value=fake_settings,
        ),
        patch(
            "api_integration.sevenrights.api.post_rfq.RfqCreateRequest.model_validate",
            return_value=fake_model,
        ),
        patch(
            "api_integration.sevenrights.api.post_rfq.retry_network",
            side_effect=_fast_retry,
        ),
        patch(
            "api_integration.sevenrights.api.post_rfq.requests.post",
            side_effect=requests.ConnectionError("NameResolutionError ..."),
        ) as mocked_post,
    ):
        result = post_rfq(data=payload)

    assert mocked_post.call_count == 3
    assert result["rfq_id"] is None
    assert "error" in result
    assert (
        "ConnectionError" in result["error"] or "NameResolutionError" in result["error"]
    )


# Non-connection RequestException is returned immediately without retries
def test_non_retryable_request_exception(fake_settings, payload):

    fake_model = MagicMock()
    fake_model.model_dump.return_value = {"title": "test"}

    with (
        patch(
            "api_integration.sevenrights.api.post_rfq.get_settings",
            return_value=fake_settings,
        ),
        patch(
            "api_integration.sevenrights.api.post_rfq.RfqCreateRequest.model_validate",
            return_value=fake_model,
        ),
        patch(
            "api_integration.sevenrights.api.post_rfq.requests.post",
            side_effect=requests.Timeout("timed out"),
        ) as mocked_post,
    ):
        result = post_rfq(data=payload)

    assert mocked_post.call_count == 1
    assert result["rfq_id"] is None
    assert "timed out" in result["error"]


# Successful API response returns rfq_id
def test_http_201_success(fake_settings, payload):

    response = MagicMock()
    response.status_code = 201
    response.json.return_value = {"id": "rfq-123"}

    fake_model = MagicMock()
    fake_model.model_dump.return_value = {"title": "test"}

    with (
        patch(
            "api_integration.sevenrights.api.post_rfq.get_settings",
            return_value=fake_settings,
        ),
        patch(
            "api_integration.sevenrights.api.post_rfq.RfqCreateRequest.model_validate",
            return_value=fake_model,
        ),
        patch(
            "api_integration.sevenrights.api.post_rfq.requests.post",
            return_value=response,
        ) as mocked_post,
    ):
        result = post_rfq(data=payload)

    assert mocked_post.call_count == 1
    assert result["error"] is None
    assert result["rfq_id"] == "rfq-123"


# API validation error is returned as error dict
def test_http_422_validation_error(fake_settings, payload):

    response = MagicMock()
    response.status_code = 422
    response.json.return_value = {"message": "invalid", "errors": {"field": "bad"}}

    fake_model = MagicMock()
    fake_model.model_dump.return_value = {"title": "test"}

    with (
        patch(
            "api_integration.sevenrights.api.post_rfq.get_settings",
            return_value=fake_settings,
        ),
        patch(
            "api_integration.sevenrights.api.post_rfq.RfqCreateRequest.model_validate",
            return_value=fake_model,
        ),
        patch(
            "api_integration.sevenrights.api.post_rfq.requests.post",
            return_value=response,
        ) as mocked_post,
    ):
        result = post_rfq(data=payload)

    assert mocked_post.call_count == 1
    assert "422" in result["error"]
    assert "invalid" in result["error"]
    assert result["rfq_id"] is None


# Server error response is returned as error dict
def test_http_500_server_error(fake_settings, payload):

    response = MagicMock()
    response.status_code = 500
    response.text = "Internal Server Error"

    fake_model = MagicMock()
    fake_model.model_dump.return_value = {"title": "test"}

    with (
        patch(
            "api_integration.sevenrights.api.post_rfq.get_settings",
            return_value=fake_settings,
        ),
        patch(
            "api_integration.sevenrights.api.post_rfq.RfqCreateRequest.model_validate",
            return_value=fake_model,
        ),
        patch(
            "api_integration.sevenrights.api.post_rfq.requests.post",
            return_value=response,
        ) as mocked_post,
    ):
        result = post_rfq(data=payload)

    assert mocked_post.call_count == 1
    assert "500" in result["error"]
    assert result["rfq_id"] is None
