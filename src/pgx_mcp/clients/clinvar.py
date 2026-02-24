"""ClinVar client via NCBI E-utilities."""

from __future__ import annotations

from typing import Any

from pgx_mcp.clients.base import BaseAPIClient
from pgx_mcp.config import Settings


class ClinVarClient(BaseAPIClient):
    """Client for ClinVar via NCBI E-utilities (https://eutils.ncbi.nlm.nih.gov)."""

    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    DEFAULT_HEADERS = {"User-Agent": "pgx-mcp/0.1.0"}

    def __init__(self, settings: Settings) -> None:
        rate = settings.clinvar_rate_limit
        if settings.ncbi_api_key:
            rate = min(rate * 3, 9.0)
        super().__init__(rate_limit=rate, cache_ttl=settings.cache_ttl_seconds)
        self._api_key = settings.ncbi_api_key

    def _base_params(self) -> dict[str, Any]:
        """Return base params including API key if configured."""
        params: dict[str, Any] = {}
        if self._api_key:
            params["api_key"] = self._api_key
        return params

    async def search_variants(
        self,
        gene: str,
        significance: str | None = None,
        max_results: int = 20,
    ) -> list[str]:
        """Search ClinVar for variants by gene and optional clinical significance.

        Returns list of ClinVar UIDs.
        """
        term_parts = [f"{gene}[gene]"]
        if significance:
            term_parts.append(f"{significance}[CLNSIG]")
        term = " AND ".join(term_parts)

        params = {
            **self._base_params(),
            "db": "clinvar",
            "term": term,
            "retmode": "json",
            "retmax": str(max_results),
        }
        data = await self.get("/esearch.fcgi", params=params)
        return data.get("esearchresult", {}).get("idlist", [])

    async def get_variant_summaries(self, uids: list[str]) -> list[dict[str, Any]]:
        """Get document summaries for ClinVar variant UIDs."""
        if not uids:
            return []
        params = {
            **self._base_params(),
            "db": "clinvar",
            "id": ",".join(uids),
            "retmode": "json",
        }
        data = await self.get("/esummary.fcgi", params=params)
        result = data.get("result", {})
        return [result[uid] for uid in uids if uid in result]

    async def lookup_variant(self, variant_name: str) -> list[dict[str, Any]]:
        """Look up a specific variant (rsID, star allele, HGVS).

        Combines esearch + esummary into a single call.
        """
        params = {
            **self._base_params(),
            "db": "clinvar",
            "term": variant_name,
            "retmode": "json",
            "retmax": "10",
        }
        search_data = await self.get("/esearch.fcgi", params=params)
        uids = search_data.get("esearchresult", {}).get("idlist", [])
        return await self.get_variant_summaries(uids)
