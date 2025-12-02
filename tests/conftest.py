from __future__ import annotations

import pytest

from lemming import org


@pytest.fixture(autouse=True)
def reset_caches():
    org.reset_caches()
    yield
    org.reset_caches()
