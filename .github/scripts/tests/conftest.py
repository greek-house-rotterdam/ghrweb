import pytest

import _common


@pytest.fixture(autouse=True)
def _no_retry_backoff(monkeypatch):
    """Make GeminiClient retry instantly so 5xx/timeout tests stay fast."""
    monkeypatch.setattr(_common, "RETRY_BACKOFF_BASE", 0)
