"""Tests for guideline tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from pgx_mcp.tools.guideline import get_dosing_guideline


def _make_ctx(app: MagicMock) -> MagicMock:
    ctx = MagicMock()
    ctx.request_context.lifespan_context = app
    return ctx


class TestGetDosingGuideline:
    async def test_found(self) -> None:
        mock_pharmgkb = AsyncMock()
        mock_pharmgkb.search_guideline_annotations.return_value = [
            {
                "id": "PA166104996",
                "name": "Annotation of CPIC Guideline for codeine and CYP2D6",
            }
        ]
        mock_pharmgkb.get_guideline_annotation.return_value = {
            "id": "PA166104996",
            "summaryMarkdown": "CYP2D6 poor metabolizers should avoid codeine.",
        }
        app = MagicMock()
        app.pharmgkb = mock_pharmgkb

        result = await get_dosing_guideline(
            ctx=_make_ctx(app), gene="CYP2D6", drug="codeine"
        )
        assert "CPIC" in result
        assert "poor metabolizers should avoid codeine" in result

    async def test_not_found(self) -> None:
        mock_pharmgkb = AsyncMock()
        mock_pharmgkb.search_guideline_annotations.return_value = []
        app = MagicMock()
        app.pharmgkb = mock_pharmgkb

        result = await get_dosing_guideline(
            ctx=_make_ctx(app), gene="CYP2D6", drug="aspirin"
        )
        assert "No CPIC/DPWG dosing guidelines found" in result
