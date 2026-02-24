"""ClinicalTrials.gov API v2 client."""

from __future__ import annotations

from typing import Any

from pgx_mcp.clients.base import BaseAPIClient
from pgx_mcp.config import Settings


class ClinicalTrialsClient(BaseAPIClient):
    """Client for ClinicalTrials.gov API v2 (https://clinicaltrials.gov/api/v2)."""

    BASE_URL = "https://clinicaltrials.gov/api/v2"
    DEFAULT_HEADERS = {"User-Agent": "pgx-mcp/0.1.0"}

    def __init__(self, settings: Settings) -> None:
        super().__init__(
            rate_limit=settings.clinical_trials_rate_limit,
            cache_ttl=settings.cache_ttl_seconds,
        )

    async def search_studies(
        self,
        condition: str | None = None,
        intervention: str | None = None,
        location: str | None = None,
        status: list[str] | None = None,
        phase: list[str] | None = None,
        page_size: int = 10,
        sort: str = "LastUpdatePostDate:desc",
    ) -> dict[str, Any]:
        """Search clinical trials.

        Covers both US and international trials registered at ClinicalTrials.gov.
        """
        params: dict[str, Any] = {
            "pageSize": page_size,
            "sort": sort,
            "countTotal": "true",
        }
        if condition:
            params["query.cond"] = condition
        if intervention:
            params["query.intr"] = intervention
        if location:
            params["query.locn"] = location
        if status:
            params["filter.overallStatus"] = ",".join(status)
        if phase:
            params["filter.phase"] = ",".join(phase)
        return await self.get("/studies", params=params)

    async def get_study(self, nct_id: str) -> dict[str, Any]:
        """Get full study details by NCT ID."""
        return await self.get(f"/studies/{nct_id}")
