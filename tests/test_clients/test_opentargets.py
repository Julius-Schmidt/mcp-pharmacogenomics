"""Tests for Open Targets client."""

from __future__ import annotations

import httpx
import pytest
import respx

from pgx_mcp.clients.opentargets import OpenTargetsClient
from pgx_mcp.config import Settings
from tests.conftest import load_fixture

BASE = "https://api.platform.opentargets.org/api/v4/graphql"


@pytest.fixture
async def client(settings: Settings) -> OpenTargetsClient:
    c = OpenTargetsClient(settings)
    await c.start()
    yield c
    await c.close()


class TestOpenTargetsClient:
    @respx.mock
    async def test_search_drug(self, client: OpenTargetsClient) -> None:
        fixture = load_fixture("opentargets", "search_drug_codeine.json")
        respx.post(BASE).mock(
            return_value=httpx.Response(200, json=fixture)
        )
        results = await client.search("codeine", entity_types=["drug"])
        assert len(results) == 1
        assert results[0]["id"] == "CHEMBL174174"

    @respx.mock
    async def test_get_drug(self, client: OpenTargetsClient) -> None:
        fixture = load_fixture("opentargets", "drug_codeine.json")
        respx.post(BASE).mock(
            return_value=httpx.Response(200, json=fixture)
        )
        result = await client.get_drug("CHEMBL174174")
        assert result is not None
        assert result["name"] == "CODEINE"
        assert len(result["pharmacogenomics"]) == 1
        assert result["pharmacogenomics"][0]["evidenceLevel"] == "1A"

    @respx.mock
    async def test_search_no_results(self, client: OpenTargetsClient) -> None:
        respx.post(BASE).mock(
            return_value=httpx.Response(
                200, json={"data": {"search": {"total": 0, "hits": []}}}
            )
        )
        results = await client.search("nonexistentdrug12345")
        assert results == []

    @respx.mock
    async def test_get_target(self, client: OpenTargetsClient) -> None:
        respx.post(BASE).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "target": {
                            "id": "ENSG00000112038",
                            "approvedSymbol": "OPRM1",
                            "approvedName": "opioid receptor mu 1",
                            "biotype": "protein_coding",
                            "tractability": [
                                {"label": "High quality pocket", "modality": "SM", "value": True}
                            ],
                        }
                    }
                },
            )
        )
        result = await client.get_target("ENSG00000112038")
        assert result is not None
        assert result["approvedSymbol"] == "OPRM1"
        assert result["biotype"] == "protein_coding"

    @respx.mock
    async def test_get_target_not_found(self, client: OpenTargetsClient) -> None:
        respx.post(BASE).mock(
            return_value=httpx.Response(200, json={"data": {"target": None}})
        )
        result = await client.get_target("ENSG00000000000")
        assert result is None

    @respx.mock
    async def test_get_target_disease_associations(self, client: OpenTargetsClient) -> None:
        respx.post(BASE).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "target": {
                            "id": "ENSG00000112038",
                            "approvedSymbol": "OPRM1",
                            "associatedDiseases": {
                                "count": 1,
                                "rows": [
                                    {
                                        "disease": {"id": "EFO_0003843", "name": "pain"},
                                        "score": 0.75,
                                        "datatypeScores": [
                                            {"id": "known_drug", "score": 0.9}
                                        ],
                                    }
                                ],
                            },
                        }
                    }
                },
            )
        )
        result = await client.get_target_disease_associations("ENSG00000112038", size=5)
        assert result is not None
        assert result["approvedSymbol"] == "OPRM1"
        assert result["associatedDiseases"]["count"] == 1
        assert result["associatedDiseases"]["rows"][0]["disease"]["name"] == "pain"
