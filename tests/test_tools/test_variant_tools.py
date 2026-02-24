"""Tests for variant tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from pgx_mcp.tools.variant import lookup_variant_clinvar, search_gene_variants_clinvar


def _make_ctx(app: MagicMock) -> MagicMock:
    ctx = MagicMock()
    ctx.request_context.lifespan_context = app
    return ctx


class TestLookupVariantClinvar:
    async def test_found(self) -> None:
        mock_clinvar = AsyncMock()
        mock_clinvar.lookup_variant.return_value = [
            {
                "uid": "12345",
                "title": "NM_000106.6(CYP2D6):c.506-1G>A",
                "clinical_significance": {
                    "description": "Pathogenic",
                    "review_status": "reviewed by expert panel",
                },
                "trait_set": [{"trait_name": "Codeine poor metabolism"}],
            }
        ]
        app = MagicMock()
        app.clinvar = mock_clinvar

        result = await lookup_variant_clinvar(ctx=_make_ctx(app), variant="CYP2D6*4")
        assert "Pathogenic" in result
        assert "CYP2D6" in result
        assert "12345" in result

    async def test_not_found(self) -> None:
        mock_clinvar = AsyncMock()
        mock_clinvar.lookup_variant.return_value = []
        app = MagicMock()
        app.clinvar = mock_clinvar

        result = await lookup_variant_clinvar(ctx=_make_ctx(app), variant="FAKE")
        assert "No ClinVar records found" in result


class TestSearchGeneVariantsClinvar:
    async def test_found(self) -> None:
        mock_clinvar = AsyncMock()
        mock_clinvar.search_variants.return_value = ["12345"]
        mock_clinvar.get_variant_summaries.return_value = [
            {
                "title": "CYP2D6 variant",
                "clinical_significance": {"description": "Pathogenic"},
            }
        ]
        app = MagicMock()
        app.clinvar = mock_clinvar

        result = await search_gene_variants_clinvar(
            ctx=_make_ctx(app), gene="CYP2D6"
        )
        assert "1 ClinVar variant" in result
        assert "Pathogenic" in result

    async def test_empty(self) -> None:
        mock_clinvar = AsyncMock()
        mock_clinvar.search_variants.return_value = []
        app = MagicMock()
        app.clinvar = mock_clinvar

        result = await search_gene_variants_clinvar(
            ctx=_make_ctx(app), gene="NONEXISTENT"
        )
        assert "No ClinVar variants found" in result
