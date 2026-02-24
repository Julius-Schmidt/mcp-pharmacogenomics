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

    @respx.mock
    async def test_get_clinical_annotation(self, client: PharmGKBClient) -> None:
        respx.get("https://api.pharmgkb.org/v1/data/clinicalAnnotation/1449309937").mock(
            return_value=httpx.Response(
                200, json={"data": {"id": 1449309937, "levelOfEvidence": {"term": "1A"}}}
            )
        )
        result = await client.get_clinical_annotation("1449309937")
        assert result["id"] == 1449309937
        assert result["levelOfEvidence"]["term"] == "1A"

    @respx.mock
    async def test_get_guideline_annotation(self, client: PharmGKBClient) -> None:
        respx.get("https://api.pharmgkb.org/v1/data/guidelineAnnotation/PA166104996").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "id": "PA166104996",
                        "name": "CPIC Guideline for codeine and CYP2D6",
                        "summaryMarkdown": {"id": 1, "html": "<p>Summary</p>"},
                    }
                },
            )
        )
        result = await client.get_guideline_annotation("PA166104996")
        assert result["id"] == "PA166104996"
        assert "CPIC" in result["name"]

    @respx.mock
    async def test_get_gene_by_symbol(self, client: PharmGKBClient) -> None:
        respx.get("https://api.pharmgkb.org/v1/data/gene").mock(
            return_value=httpx.Response(
                200, json={"data": [{"id": "PA128", "symbol": "CYP2D6"}]}
            )
        )
        result = await client.get_gene("CYP2D6")
        assert result["symbol"] == "CYP2D6"
        assert result["id"] == "PA128"

    @respx.mock
    async def test_get_gene_by_pa_id(self, client: PharmGKBClient) -> None:
        respx.get("https://api.pharmgkb.org/v1/data/gene/PA128").mock(
            return_value=httpx.Response(
                200, json={"data": {"id": "PA128", "symbol": "CYP2D6"}}
            )
        )
        result = await client.get_gene("PA128")
        assert result["symbol"] == "CYP2D6"

    @respx.mock
    async def test_get_gene_not_found(self, client: PharmGKBClient) -> None:
        respx.get("https://api.pharmgkb.org/v1/data/gene").mock(
            return_value=httpx.Response(200, json={"data": []})
        )
        result = await client.get_gene("FAKEGENE")
        assert result == {}

    @respx.mock
    async def test_get_variant(self, client: PharmGKBClient) -> None:
        respx.get("https://api.pharmgkb.org/v1/data/variant/rs3892097").mock(
            return_value=httpx.Response(
                200, json={"data": {"id": "PA166153760", "name": "rs3892097"}}
            )
        )
        result = await client.get_variant("rs3892097")
        assert result["name"] == "rs3892097"

    @respx.mock
    async def test_search_variant_annotations(self, client: PharmGKBClient) -> None:
        respx.get("https://api.pharmgkb.org/v1/data/variantAnnotation").mock(
            return_value=httpx.Response(
                200,
                json={"data": [{"id": "ann1", "variant": "rs3892097"}]},
            )
        )
        result = await client.search_variant_annotations(variant="rs3892097", gene="CYP2D6")
        assert len(result) == 1
        assert result[0]["variant"] == "rs3892097"

    @respx.mock
    async def test_search_variant_annotations_empty(self, client: PharmGKBClient) -> None:
        respx.get("https://api.pharmgkb.org/v1/data/variantAnnotation").mock(
            return_value=httpx.Response(200, json={"data": []})
        )
        result = await client.search_variant_annotations(gene="NONEXISTENT")
        assert result == []
