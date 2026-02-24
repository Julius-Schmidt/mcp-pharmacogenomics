"""Tests for gnomAD client."""

from __future__ import annotations

import httpx
import pytest
import respx

from pgx_mcp.clients.gnomad import GnomADClient
from pgx_mcp.config import Settings
from tests.conftest import load_fixture

BASE = "https://gnomad.broadinstitute.org/api/"


@pytest.fixture
async def client(settings: Settings) -> GnomADClient:
    c = GnomADClient(settings)
    await c.start()
    yield c
    await c.close()


class TestGnomADClient:
    @respx.mock
    async def test_get_variant(self, client: GnomADClient) -> None:
        fixture = load_fixture("gnomad", "variant_rs3892097.json")
        respx.post(BASE).mock(
            return_value=httpx.Response(200, json=fixture)
        )
        result = await client.get_variant("22-42126611-C-T")
        assert result is not None
        assert result["variant_id"] == "22-42126611-C-T"
        assert result["exome"]["af"] == 0.034
        assert len(result["exome"]["populations"]) == 4

    @respx.mock
    async def test_get_variant_not_found(self, client: GnomADClient) -> None:
        respx.post(BASE).mock(
            return_value=httpx.Response(200, json={"data": {"variant": None}})
        )
        result = await client.get_variant("1-1-A-T")
        assert result is None

    @respx.mock
    async def test_get_gene_variants(self, client: GnomADClient) -> None:
        respx.post(BASE).mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": {
                        "gene": {
                            "gene_id": "ENSG00000100197",
                            "symbol": "CYP2D6",
                            "variants": [
                                {
                                    "variant_id": "22-42126611-C-T",
                                    "pos": 42126611,
                                    "exome": {"ac": 100, "an": 5000, "af": 0.02},
                                    "genome": {"ac": 50, "an": 3000, "af": 0.017},
                                }
                            ],
                        }
                    }
                },
            )
        )
        result = await client.get_gene_variants("CYP2D6")
        assert result is not None
        assert result["symbol"] == "CYP2D6"
        assert len(result["variants"]) == 1
        assert result["variants"][0]["variant_id"] == "22-42126611-C-T"

    @respx.mock
    async def test_get_gene_variants_not_found(self, client: GnomADClient) -> None:
        respx.post(BASE).mock(
            return_value=httpx.Response(200, json={"data": {"gene": None}})
        )
        result = await client.get_gene_variants("FAKEGENE")
        assert result is None
