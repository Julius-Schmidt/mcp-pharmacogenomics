"""Open Targets Platform GraphQL client for drug-target-disease associations."""

from __future__ import annotations

from typing import Any

from pgx_mcp.clients.base import BaseAPIClient
from pgx_mcp.config import Settings


def _gql_str(value: str) -> str:
    """Escape a string for inline GraphQL use."""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


class OpenTargetsClient(BaseAPIClient):
    """Client for Open Targets Platform GraphQL API.

    Note: The Open Targets API does not support standard GraphQL variables,
    so all queries use inline values.
    """

    BASE_URL = "https://api.platform.opentargets.org/api/v4/"
    DEFAULT_HEADERS = {
        "Content-Type": "application/json",
        "User-Agent": "pgx-mcp/0.1.0",
    }

    def __init__(self, settings: Settings) -> None:
        super().__init__(
            rate_limit=settings.opentargets_rate_limit,
            cache_ttl=settings.cache_ttl_seconds,
        )

    async def _graphql(self, query: str) -> Any:
        """Execute a GraphQL query against Open Targets."""
        return await self.post("graphql", json={"query": query})

    async def search(
        self,
        query_string: str,
        entity_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for targets, diseases, or drugs by name."""
        entity_filter = ""
        if entity_types:
            names = ", ".join(_gql_str(t) for t in entity_types)
            entity_filter = f", entityNames: [{names}]"
        query = (
            "{ search("
            f"queryString: {_gql_str(query_string)}"
            f"{entity_filter}, "
            "page: {size: 10, index: 0}"
            ") { total hits { id entity name description } } }"
        )
        data = await self._graphql(query)
        return data.get("data", {}).get("search", {}).get("hits", [])

    async def get_drug(self, chembl_id: str) -> dict[str, Any] | None:
        """Get drug info including mechanisms, indications, and PGx data."""
        query = (
            "{ drug(chemblId: " + _gql_str(chembl_id) + ") {"
            " id name drugType"
            " mechanismsOfAction { rows { mechanismOfAction"
            " targets { id approvedSymbol } } }"
            " indications { rows { disease { id name }"
            " maxPhaseForIndication } }"
            " pharmacogenomics { variantRsId genotype"
            " variantFunctionalConsequenceId phenotypeText"
            " isDirectTarget genotypeAnnotationText literature"
            " pgxCategory targetFromSourceId evidenceLevel }"
            " } }"
        )
        data = await self._graphql(query)
        return data.get("data", {}).get("drug")

    async def get_target(self, ensembl_id: str) -> dict[str, Any] | None:
        """Get target/gene info from Open Targets."""
        query = (
            "{ target(ensemblId: " + _gql_str(ensembl_id) + ") {"
            " id approvedSymbol approvedName biotype"
            " tractability { label modality value }"
            " } }"
        )
        data = await self._graphql(query)
        return data.get("data", {}).get("target")

    async def get_target_disease_associations(
        self,
        ensembl_id: str,
        size: int = 10,
    ) -> dict[str, Any] | None:
        """Get disease associations for a gene/target."""
        query = (
            "{ target(ensemblId: " + _gql_str(ensembl_id) + ") {"
            " id approvedSymbol"
            f" associatedDiseases(page: {{size: {size}, index: 0}}) {{"
            " count rows { disease { id name } score"
            " datatypeScores { id score } } }"
            " } }"
        )
        data = await self._graphql(query)
        return data.get("data", {}).get("target")
