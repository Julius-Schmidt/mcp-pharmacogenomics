"""Shared test fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from pgx_mcp.config import Settings

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(subdir: str, filename: str) -> dict[str, Any]:
    """Load a JSON fixture file."""
    with open(FIXTURES_DIR / subdir / filename) as f:
        return json.load(f)


@pytest.fixture
def settings() -> Settings:
    """Settings with caching disabled and high rate limits for tests."""
    return Settings(
        cache_ttl_seconds=0,
        pharmgkb_rate_limit=100,
        clinvar_rate_limit=100,
        gnomad_rate_limit=100,
        opentargets_rate_limit=100,
        clinical_trials_rate_limit=100,
    )
