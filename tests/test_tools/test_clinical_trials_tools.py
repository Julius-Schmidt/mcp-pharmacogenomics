"""Tests for clinical trial tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

from pgx_mcp.tools.clinical_trials import get_trial_details, search_clinical_trials


def _make_ctx(app: MagicMock) -> MagicMock:
    ctx = MagicMock()
    ctx.request_context.lifespan_context = app
    return ctx


class TestSearchClinicalTrials:
    async def test_found(self) -> None:
        mock_ct = AsyncMock()
        mock_ct.search_studies.return_value = {
            "totalCount": 1,
            "studies": [
                {
                    "protocolSection": {
                        "identificationModule": {
                            "nctId": "NCT04267848",
                            "briefTitle": "PGx-Guided Codeine Prescribing",
                        },
                        "statusModule": {"overallStatus": "RECRUITING"},
                        "designModule": {"phases": ["PHASE3"]},
                        "descriptionModule": {
                            "briefSummary": "A study on PGx-guided prescribing."
                        },
                    }
                }
            ],
        }
        app = MagicMock()
        app.clinical_trials = mock_ct

        result = await search_clinical_trials(
            ctx=_make_ctx(app), condition="pharmacogenomics"
        )
        assert "NCT04267848" in result
        assert "RECRUITING" in result
        assert "PHASE3" in result

    async def test_empty(self) -> None:
        mock_ct = AsyncMock()
        mock_ct.search_studies.return_value = {"totalCount": 0, "studies": []}
        app = MagicMock()
        app.clinical_trials = mock_ct

        result = await search_clinical_trials(
            ctx=_make_ctx(app), condition="nonexistent"
        )
        assert "No clinical trials found" in result


class TestGetTrialDetails:
    async def test_found(self) -> None:
        mock_ct = AsyncMock()
        mock_ct.get_study.return_value = {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT04267848",
                    "officialTitle": "Full Trial Title Here",
                    "briefTitle": "Short Title",
                },
                "statusModule": {"overallStatus": "RECRUITING"},
                "descriptionModule": {
                    "briefSummary": "Study summary.",
                    "detailedDescription": "Detailed study description.",
                },
                "eligibilityModule": {
                    "eligibilityCriteria": "Ages 18+, CYP2D6 poor metabolizer"
                },
                "contactsLocationsModule": {
                    "locations": [
                        {
                            "facility": "University Hospital",
                            "city": "Berlin",
                            "country": "Germany",
                        }
                    ]
                },
                "armsInterventionsModule": {
                    "interventions": [
                        {"name": "Codeine", "type": "Drug"}
                    ]
                },
            }
        }
        app = MagicMock()
        app.clinical_trials = mock_ct

        result = await get_trial_details(
            ctx=_make_ctx(app), nct_id="NCT04267848"
        )
        assert "NCT04267848" in result
        assert "Full Trial Title Here" in result
        assert "Berlin" in result
        assert "Codeine" in result
