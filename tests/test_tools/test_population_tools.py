"""Tests for population frequency tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from pgx_mcp.tools.population import get_variant_frequency


def _make_ctx(app: MagicMock) -> MagicMock:
    ctx = MagicMock()
    ctx.request_context.lifespan_context = app
    return ctx


class TestGetVariantFrequency:
    async def test_found(self) -> None:
        mock_gnomad = AsyncMock()
        mock_gnomad.get_variant.return_value = {
            "variant_id": "22-42126611-C-T",
            "reference_genome": "GRCh38",
            "chrom": "22",
            "pos": 42126611,
            "exome": {
                "ac": 8500,
                "an": 250000,
                "af": 0.034,
                "populations": [
                    {"id": "eur", "ac": 5000, "an": 130000},
                    {"id": "afr", "ac": 200, "an": 16000},
                ],
            },
            "genome": None,
        }
        app = MagicMock()
        app.gnomad = mock_gnomad

        result = await get_variant_frequency(
            ctx=_make_ctx(app), variant_id="22-42126611-C-T"
        )
        assert "22-42126611-C-T" in result
        assert "GRCh38" in result
        assert "Exome Data" in result
        assert "eur" in result

    async def test_not_found(self) -> None:
        mock_gnomad = AsyncMock()
        mock_gnomad.get_variant.return_value = None
        app = MagicMock()
        app.gnomad = mock_gnomad

        result = await get_variant_frequency(
            ctx=_make_ctx(app), variant_id="1-1-A-T"
        )
        assert "not found in gnomAD" in result
