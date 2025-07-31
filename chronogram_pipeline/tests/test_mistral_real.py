import os
import pytest
from pathlib import Path

# Import the _default_mistral_call helper from standardizer
from src.standardizer import _default_mistral_call

@pytest.mark.integration
def test_mistral_real_call_header():
    """Call the real Mistral API to map a header."""
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        pytest.skip("MISTRAL_API_KEY not configured")

    allowed = ["type_inject", "label"]
    try:
        response = _default_mistral_call("L", allowed)
    except Exception as exc:
        pytest.skip(f"Mistral API call failed: {exc}")

    assert response in allowed
