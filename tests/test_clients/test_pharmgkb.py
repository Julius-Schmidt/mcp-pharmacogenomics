"""Tests for PharmGKB client."""

from __future__ import annotations

import httpx
import pytest
import respx

from pgx_mcp.clients.pharmgkb import PharmGKBClient
from pgx_mcp.config import Settings
from tests.conftest import load_fixture


@pytest.fixture
async def client(settings: Settings) -> PharmGKBClient:
    c = PharmGKBClient(settings)
    await c.start()
    yield c
    await c.close()


class TestPharmGKBClient:
    @respx.mock
    async def test_search_clinical_annotations(self, client: PharmGKBClient) -> None:
        fixture = load_fixture("pharmgkb", "clinical_annotation_cyp2d6.json")
        respx.get("https://api.pharmgkb.org/v1/data/clinicalAnnotation").mock(
            return_value=httpx.Response(200, json=fixture)
        )
        result = await client.search_clinical_annotations(gene="CYP2D6", chemical="codeine")
        assert len(result) == 2
        assert result[0]["levelOfEvidence"]["term"] == "1A"

    @respx.mock
    async def test_search_clinical_annotations_empty(self, client: PharmGKBClient) -> None:
        respx.get("https://api.pharmgkb.org/v1/data/clinicalAnnotation").mock(
            return_value=httpx.Response(200, json={"data": []})
        )
        result = await client.search_clinical_annotations(gene="NONEXISTENT")
        assert result == []

    @respx.mock
    async def test_search_chemicals(self, client: PharmGKBClient) -> None:
        fixture = load_fixture("pharmgkb", "search_chemicals_codeine.json")
        respx.get("https://api.pharmgkb.org/v1/data/chemical").mock(
            return_value=httpx.Response(200, json=fixture)
        )
        result = await client.search_chemicals("codeine")
        assert len(result) == 1
        assert result[0]["name"] == "codeine"

    @respx.mock
    async def test_get_chemical(self, client: PharmGKBClient) -> None:
        fixture = load_fixture("pharmgkb", "chemical_codeine.json")
        respx.get("https://api.pharmgkb.org/v1/data/chemical/PA449088").mock(
            return_value=httpx.Response(200, json=fixture)
        )
        result = await client.get_chemical("PA449088")
        assert result["name"] == "codeine"
        assert result["id"] == "PA449088"

    @respx.mock
    async def test_search_guideline_annotations(self, client: PharmGKBClient) -> None:
        fixture = load_fixture("pharmgkb", "guideline_cpic_cyp2d6_codeine.json")
        respx.get("https://api.pharmgkb.org/v1/data/guidelineAnnotation").mock(
            return_value=httpx.Response(200, json=fixture)
        )
        result = await client.search_guideline_annotations(gene="CYP2D6", chemical="codeine")
        assert len(result) == 1
        assert "CPIC" in result[0]["name"]
