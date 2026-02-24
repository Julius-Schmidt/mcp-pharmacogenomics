"""Tests for drug tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from pgx_mcp.tools.drug import get_drug_gene_interactions, get_drug_info, search_drug_targets


def _make_ctx(app: MagicMock) -> MagicMock:
    ctx = MagicMock()
    ctx.request_context.lifespan_context = app
    return ctx


class TestGetDrugGeneInteractions:
    async def test_found(self) -> None:
        mock_pharmgkb = AsyncMock()
        mock_pharmgkb.search_clinical_annotations.return_value = [
            {
                "id": 123,
                "levelOfEvidence": {"term": "1A"},
                "types": ["Toxicity/ADR"],
                "location": {"displayName": "CYP2D6*4"},
            }
        ]
        app = MagicMock()
        app.pharmgkb = mock_pharmgkb

        result = await get_drug_gene_interactions(
            ctx=_make_ctx(app), drug="codeine", gene="CYP2D6"
        )
        assert "Level 1A" in result
        assert "codeine" in result

    async def test_not_found(self) -> None:
        mock_pharmgkb = AsyncMock()
        mock_pharmgkb.search_clinical_annotations.return_value = []
        app = MagicMock()
        app.pharmgkb = mock_pharmgkb

        result = await get_drug_gene_interactions(
            ctx=_make_ctx(app), drug="nonexistent"
        )
        assert "No clinical annotations found" in result


class TestGetDrugInfo:
    async def test_found(self) -> None:
        mock_pharmgkb = AsyncMock()
        mock_pharmgkb.search_chemicals.return_value = [{"id": "PA449088", "name": "codeine"}]
        mock_pharmgkb.get_chemical.return_value = {
            "id": "PA449088",
            "name": "codeine",
            "genericNames": ["codeine phosphate"],
            "tradeNames": ["Tylenol with Codeine"],
        }
        app = MagicMock()
        app.pharmgkb = mock_pharmgkb

        result = await get_drug_info(ctx=_make_ctx(app), drug="codeine")
        assert "codeine" in result
        assert "PA449088" in result

    async def test_not_found(self) -> None:
        mock_pharmgkb = AsyncMock()
        mock_pharmgkb.search_chemicals.return_value = []
        app = MagicMock()
        app.pharmgkb = mock_pharmgkb

        result = await get_drug_info(ctx=_make_ctx(app), drug="nonexistent")
        assert "No drug/chemical found" in result


class TestSearchDrugTargets:
    async def test_found(self) -> None:
        mock_opentargets = AsyncMock()
        mock_opentargets.search.return_value = [
            {"id": "CHEMBL174174", "name": "CODEINE"}
        ]
        mock_opentargets.get_drug.return_value = {
            "name": "CODEINE",
            "drugType": "Small molecule",
            "mechanismsOfAction": {
                "rows": [
                    {
                        "mechanismOfAction": "Opioid receptor agonist",
                        "targets": [{"approvedSymbol": "OPRM1"}],
                    }
                ]
            },
            "pharmacogenomics": [
                {
                    "variantRsId": "rs3892097",
                    "genotype": "CC",
                    "phenotypeText": "decreased function",
                    "evidenceLevel": "1A",
                }
            ],
        }
        app = MagicMock()
        app.opentargets = mock_opentargets

        result = await search_drug_targets(ctx=_make_ctx(app), drug_name="codeine")
        assert "CODEINE" in result
        assert "Opioid receptor agonist" in result
        assert "rs3892097" in result

    async def test_not_found(self) -> None:
        mock_opentargets = AsyncMock()
        mock_opentargets.search.return_value = []
        app = MagicMock()
        app.opentargets = mock_opentargets

        result = await search_drug_targets(
            ctx=_make_ctx(app), drug_name="nonexistent"
        )
        assert "No drug found" in result
