"""Tests for ClinVar client."""

from __future__ import annotations

import httpx
import pytest
import respx

from pgx_mcp.clients.clinvar import ClinVarClient
from pgx_mcp.config import Settings
from tests.conftest import load_fixture

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


@pytest.fixture
async def client(settings: Settings) -> ClinVarClient:
    c = ClinVarClient(settings)
    await c.start()
    yield c
    await c.close()


class TestClinVarClient:
    @respx.mock
    async def test_search_variants(self, client: ClinVarClient) -> None:
        fixture = load_fixture("clinvar", "esearch_cyp2d6.json")
        respx.get(f"{BASE}/esearch.fcgi").mock(
            return_value=httpx.Response(200, json=fixture)
        )
        uids = await client.search_variants("CYP2D6")
        assert uids == ["12345", "12346"]

    @respx.mock
    async def test_search_variants_empty(self, client: ClinVarClient) -> None:
        respx.get(f"{BASE}/esearch.fcgi").mock(
            return_value=httpx.Response(
                200, json={"esearchresult": {"count": "0", "idlist": []}}
            )
        )
        uids = await client.search_variants("NONEXISTENT")
        assert uids == []

    @respx.mock
    async def test_get_variant_summaries(self, client: ClinVarClient) -> None:
        fixture = load_fixture("clinvar", "esummary_variant.json")
        respx.get(f"{BASE}/esummary.fcgi").mock(
            return_value=httpx.Response(200, json=fixture)
        )
        summaries = await client.get_variant_summaries(["12345", "12346"])
        assert len(summaries) == 2
        assert summaries[0]["uid"] == "12345"
        assert summaries[0]["clinical_significance"]["description"] == "Pathogenic"

    async def test_get_variant_summaries_empty(self, client: ClinVarClient) -> None:
        result = await client.get_variant_summaries([])
        assert result == []

    @respx.mock
    async def test_lookup_variant(self, client: ClinVarClient) -> None:
        search_fixture = load_fixture("clinvar", "esearch_cyp2d6.json")
        summary_fixture = load_fixture("clinvar", "esummary_variant.json")
        respx.get(f"{BASE}/esearch.fcgi").mock(
            return_value=httpx.Response(200, json=search_fixture)
        )
        respx.get(f"{BASE}/esummary.fcgi").mock(
            return_value=httpx.Response(200, json=summary_fixture)
        )
        results = await client.lookup_variant("CYP2D6*4")
        assert len(results) == 2
        assert "Pathogenic" in results[0]["clinical_significance"]["description"]

    async def test_api_key_included(self, settings: Settings) -> None:
        settings.ncbi_api_key = "test_key_123"
        c = ClinVarClient(settings)
        params = c._base_params()
        assert params["api_key"] == "test_key_123"
