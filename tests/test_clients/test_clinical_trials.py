"""Tests for ClinicalTrials.gov client."""

from __future__ import annotations

import httpx
import pytest
import respx

from pgx_mcp.clients.clinical_trials import ClinicalTrialsClient
from pgx_mcp.config import Settings
from tests.conftest import load_fixture

BASE = "https://clinicaltrials.gov/api/v2"


@pytest.fixture
async def client(settings: Settings) -> ClinicalTrialsClient:
    c = ClinicalTrialsClient(settings)
    await c.start()
    yield c
    await c.close()


class TestClinicalTrialsClient:
    @respx.mock
    async def test_search_studies(self, client: ClinicalTrialsClient) -> None:
        fixture = load_fixture("clinical_trials", "studies_pharmacogenomics.json")
        respx.get(f"{BASE}/studies").mock(
            return_value=httpx.Response(200, json=fixture)
        )
        result = await client.search_studies(condition="pharmacogenomics CYP2D6")
        assert result["totalCount"] == 2
        assert len(result["studies"]) == 2

    @respx.mock
    async def test_search_studies_with_filters(self, client: ClinicalTrialsClient) -> None:
        fixture = load_fixture("clinical_trials", "studies_pharmacogenomics.json")
        respx.get(f"{BASE}/studies").mock(
            return_value=httpx.Response(200, json=fixture)
        )
        result = await client.search_studies(
            condition="CYP2D6",
            location="Germany",
            status=["RECRUITING"],
            phase=["PHASE3"],
        )
        assert "studies" in result

    @respx.mock
    async def test_search_studies_empty(self, client: ClinicalTrialsClient) -> None:
        respx.get(f"{BASE}/studies").mock(
            return_value=httpx.Response(
                200, json={"totalCount": 0, "studies": []}
            )
        )
        result = await client.search_studies(condition="nonexistent12345")
        assert result["totalCount"] == 0
        assert result["studies"] == []
