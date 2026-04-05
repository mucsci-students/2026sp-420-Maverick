# Author: Antonio Corona
# Date: 2026-04-05
"""
test_openai_client.py

Tests for app/web/services/openai_client.py.

Purpose:
- Verify OpenAI client creation behavior
- Verify missing-key handling
- Verify model selection behavior
- Confirm config helper integration works as expected
"""

from app.web.services.openai_client import get_openai_client, get_model_name


def test_get_openai_client_raises_without_api_key(monkeypatch):
    """
    Ensures client helper raises a clear error if no API key is available
    from either local settings or environment variables.
    """
    monkeypatch.setattr(
        "app.web.services.openai_client.get_openai_api_key",
        lambda: None,
    )

    try:
        get_openai_client()
        assert False, "Expected ValueError when no OpenAI API key is configured"
    except ValueError as e:
        assert "Missing OpenAI API key" in str(e)


def test_get_openai_client_returns_client_with_api_key(monkeypatch):
    """
    Ensures client helper constructs the OpenAI client with the resolved API key.
    """
    captured = {"api_key": None}

    class FakeOpenAI:
        def __init__(self, api_key):
            captured["api_key"] = api_key

    monkeypatch.setattr(
        "app.web.services.openai_client.get_openai_api_key",
        lambda: "test-key",
    )
    monkeypatch.setattr(
        "app.web.services.openai_client.OpenAI",
        FakeOpenAI,
    )

    client = get_openai_client()

    assert captured["api_key"] == "test-key"
    assert client is not None


def test_get_model_name_returns_resolved_model(monkeypatch):
    """
    Ensures model helper returns the resolved model from configuration.
    """
    monkeypatch.setattr(
        "app.web.services.openai_client.get_openai_model",
        lambda: "gpt-5.1-mini",
    )

    assert get_model_name() == "gpt-5.1-mini"


def test_get_model_name_falls_back_to_default_when_helper_returns_default(monkeypatch):
    """
    Ensures the default model path still works as expected.
    """
    monkeypatch.setattr(
        "app.web.services.openai_client.get_openai_model",
        lambda: "gpt-5-mini",
    )

    assert get_model_name() == "gpt-5-mini"