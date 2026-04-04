# Author: Antonio Corona
# Date: 2026-04-04
"""
test_openai_client.py

Tests for app/web/services/openai_client.py.

Purpose:
- Validate OpenAI client creation behavior
- Confirm model-name resolution from environment variables

These are base-case utility tests designed to:
- Improve coverage for external API setup helpers
- Protect environment-variable configuration logic
- Avoid direct real API calls by monkeypatching the SDK client
"""

from app.web.services.openai_client import get_model_name, get_openai_client


def test_get_openai_client_raises_without_api_key(monkeypatch):
    """
    Ensures client helper raises a clear error if API key is missing.
    """
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    try:
        get_openai_client()
        assert False, "Expected ValueError when OPENAI_API_KEY is missing"
    except ValueError as exc:
        assert "Missing OPENAI_API_KEY environment variable" in str(exc)


def test_get_openai_client_returns_client_with_api_key(monkeypatch):
    """
    Ensures client helper constructs the OpenAI client when API key exists.
    """
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    captured = {"api_key": None}

    class FakeOpenAI:
        """
        Fake replacement for the SDK OpenAI client class.
        """
        def __init__(self, api_key):
            captured["api_key"] = api_key

    monkeypatch.setattr(
        "app.web.services.openai_client.OpenAI",
        FakeOpenAI,
    )

    client = get_openai_client()

    assert captured["api_key"] == "test-key"
    assert isinstance(client, FakeOpenAI)


def test_get_model_name_returns_default(monkeypatch):
    """
    Ensures model helper falls back to default model when env var is absent.
    """
    monkeypatch.delenv("MAVERICK_OPENAI_MODEL", raising=False)

    assert get_model_name() == "gpt-5-mini"


def test_get_model_name_returns_env_override(monkeypatch):
    """
    Ensures model helper returns the environment override when provided.
    """
    monkeypatch.setenv("MAVERICK_OPENAI_MODEL", "gpt-5.1-mini")

    assert get_model_name() == "gpt-5.1-mini"