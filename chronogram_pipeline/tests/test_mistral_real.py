import os
from pathlib import Path
from typing import Any

import pytest
import requests

from src.standardizer import _default_mistral_call


class _DummyResponse:
    """Minimal response object for mocking ``requests.post``."""

    def __init__(self, content: str) -> None:
        self._content = content

    def raise_for_status(self) -> None:  # pragma: no cover - no failure expected
        pass

    def json(self) -> Any:  # pragma: no cover - deterministic
        return {"choices": [{"message": {"content": self._content}}]}


@pytest.mark.integration
def test_mistral_real_call_header(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulate a Mistral API call to map a header."""
    allowed = ["type_inject", "label"]

    def fake_post(*args: Any, **kwargs: Any) -> _DummyResponse:
        return _DummyResponse(allowed[0])

    # Ensure the function sees an API key and use the fake request
    monkeypatch.setenv("MISTRAL_API_KEY", "dummy-key")
    monkeypatch.setattr(requests, "post", fake_post)

    response = _default_mistral_call("L", allowed)
    assert response in allowed
