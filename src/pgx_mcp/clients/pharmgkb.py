"""PharmGKB API client for drug-gene interactions and CPIC guidelines."""

from __future__ import annotations

from typing import Any

from pgx_mcp.clients.base import BaseAPIClient
from pgx_mcp.config import Settings


class PharmGKBClient(BaseAPIClient):
    """Client for the PharmGKB REST API (https://api.pharmgkb.org)."""

    BASE_URL = "https://api.pharmgkb.org"
    DEFAULT_HEADERS = {
        "Accept": "application/json",
        "User-Agent": "pgx-mcp/0.1.0",
    }

    def __init__(self, settings: Settings) -> None:
        super().__init__(
            rate_limit=settings.pharmgkb_rate_limit,
            cache_ttl=settings.cache_ttl_seconds,
        )

    async def search_clinical_annotations(
        self,
        gene: str | None = None,
        chemical: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search clinical annotations by gene and/or chemical name."""
        params: dict[str, Any] = {"view": "min"}
        if gene:
            params["location.genes.symbol"] = gene
        if chemical:
            params["relatedChemicals.name"] = chemical
        data = await self.get("/v1/data/clinicalAnnotation", params=params)
        return data.get("data", [])

    async def get_clinical_annotation(self, annotation_id: str) -> dict[str, Any]:
        """Get a specific clinical annotation by ID."""
        data = await self.get(f"/v1/data/clinicalAnnotation/{annotation_id}")
        return data.get("data", {})

    async def search_guideline_annotations(
        self,
        gene: str | None = None,
        chemical: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search CPIC/DPWG guideline annotations."""
        params: dict[str, Any] = {"view": "min"}
        if gene:
            params["relatedGenes.symbol"] = gene
        if chemical:
            params["relatedChemicals.name"] = chemical
        data = await self.get("/v1/data/guidelineAnnotation", params=params)
        return data.get("data", [])

    async def get_guideline_annotation(self, guideline_id: str) -> dict[str, Any]:
        """Get full CPIC/DPWG guideline by ID."""
        data = await self.get(f"/v1/data/guidelineAnnotation/{guideline_id}")
        return data.get("data", {})

    async def get_chemical(self, name_or_id: str) -> dict[str, Any]:
        """Get chemical/drug information by PharmGKB ID or name."""
        data = await self.get(f"/v1/data/chemical/{name_or_id}")
        return data.get("data", {})

    async def search_chemicals(self, query: str) -> list[dict[str, Any]]:
        """Search chemicals by name."""
        data = await self.get(
            "/v1/data/chemical", params={"name": query, "view": "min"}
        )
        return data.get("data", [])

    async def get_gene(self, symbol_or_id: str) -> dict[str, Any]:
        """Get gene information by symbol or PharmGKB ID."""
        if symbol_or_id.startswith("PA"):
            # Direct lookup by PharmGKB accession ID
            data = await self.get(f"/v1/data/gene/{symbol_or_id}")
            return data.get("data", {})
        # Search by gene symbol
        data = await self.get(
            "/v1/data/gene", params={"symbol": symbol_or_id, "view": "min"}
        )
        results = data.get("data", [])
        return results[0] if results else {}

    async def get_variant(self, variant_id: str) -> dict[str, Any]:
        """Get variant information by rsID or PharmGKB ID."""
        data = await self.get(f"/v1/data/variant/{variant_id}")
        return data.get("data", {})

    async def search_variant_annotations(
        self,
        variant: str | None = None,
        gene: str | None = None,
    ) -> list[dict[str, Any]]:
        """Search variant annotations."""
        params: dict[str, Any] = {"view": "min"}
        if variant:
            params["variant"] = variant
        if gene:
            params["gene"] = gene
        data = await self.get("/v1/data/variantAnnotation", params=params)
        return data.get("data", [])
