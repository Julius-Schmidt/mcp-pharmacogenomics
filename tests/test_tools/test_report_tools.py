"""Tests for composite pgx_consultation tool."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from pgx_mcp.tools.report import _parse_alleles, pgx_consultation


def _make_ctx(app: MagicMock) -> MagicMock:
    ctx = MagicMock()
    ctx.request_context.lifespan_context = app
    return ctx


class TestParseAlleles:
    def test_standard_diplotype(self) -> None:
        assert _parse_alleles("*1/*4") == ["*1", "*4"]

    def test_homozygous(self) -> None:
        assert _parse_alleles("*4/*4") == ["*4", "*4"]

    def test_with_spaces(self) -> None:
        assert _parse_alleles("*1 / *4") == ["*1", "*4"]

    def test_single(self) -> None:
        assert _parse_alleles("*4") == ["*4"]


class TestPgxConsultation:
    async def test_basic_consultation(self) -> None:
        mock_pharmgkb = AsyncMock()
        mock_pharmgkb.get_gene.return_value = {"id": "PA128", "name": "CYP2D6"}
        mock_pharmgkb.search_clinical_annotations.return_value = [
            {
                "id": 123,
                "levelOfEvidence": {"term": "1A"},
                "types": ["Toxicity/ADR"],
                "location": {"displayName": "CYP2D6*4"},
            }
        ]
        mock_pharmgkb.search_guideline_annotations.return_value = [
            {
                "id": "PA166104996",
                "name": "Annotation of CPIC Guideline for codeine and CYP2D6",
            }
        ]
        mock_pharmgkb.get_guideline_annotation.return_value = {
            "summaryMarkdown": "Avoid codeine in poor metabolizers."
        }

        mock_clinvar = AsyncMock()
        mock_clinvar.lookup_variant.return_value = [
            {
                "clinical_significance": {"description": "Pathogenic"},
            }
        ]

        mock_ct = AsyncMock()
        mock_ct.search_studies.return_value = {"studies": []}

        app = MagicMock()
        app.pharmgkb = mock_pharmgkb
        app.clinvar = mock_clinvar
        app.clinical_trials = mock_ct

        result = await pgx_consultation(
            ctx=_make_ctx(app),
            gene="CYP2D6",
            diplotype="*4/*4",
            drug="codeine",
            clinical_context="pain management",
        )

        assert "Pharmacogenomics Consultation" in result
        assert "CYP2D6" in result
        assert "codeine" in result
        assert "pain management" in result
        assert "Level 1A" in result
        assert "Dosing Guidelines" in result
        assert "Disclaimer" in result

    async def test_consultation_no_drug(self) -> None:
        mock_pharmgkb = AsyncMock()
        mock_pharmgkb.get_gene.return_value = {"id": "PA128"}
        mock_pharmgkb.search_clinical_annotations.return_value = []

        mock_clinvar = AsyncMock()
        mock_clinvar.lookup_variant.return_value = []

        mock_ct = AsyncMock()
        mock_ct.search_studies.return_value = {"studies": []}

        app = MagicMock()
        app.pharmgkb = mock_pharmgkb
        app.clinvar = mock_clinvar
        app.clinical_trials = mock_ct

        result = await pgx_consultation(
            ctx=_make_ctx(app),
            gene="CYP2D6",
            diplotype="*1/*4",
        )

        assert "CYP2D6" in result
        assert "Disclaimer" in result
        # No drug specified, so no dosing guidelines section
        assert "Dosing Guidelines" not in result
