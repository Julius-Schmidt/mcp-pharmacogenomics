"""gnomAD GraphQL client for population allele frequencies."""

from __future__ import annotations

from typing import Any

from pgx_mcp.clients.base import BaseAPIClient
from pgx_mcp.config import Settings

VARIANT_QUERY = """
query VariantDetails($variantId: String!, $dataset: DatasetId!) {
  variant(variantId: $variantId, dataset: $dataset) {
    variant_id
    reference_genome
    chrom
    pos
    ref
    alt
    exome {
      ac
      an
      af
      ac_hom
      populations {
        id
        ac
        an
        ac_hom
      }
    }
    genome {
      ac
      an
      af
      ac_hom
      populations {
        id
        ac
        an
        ac_hom
      }
    }
  }
}
"""

GENE_VARIANTS_QUERY = """
query GeneVariants(
  $geneSymbol: String!, $dataset: DatasetId!, $referenceGenome: ReferenceGenomeId!
) {
  gene(gene_symbol: $geneSymbol, reference_genome: $referenceGenome) {
    gene_id
    symbol
    variants(dataset: $dataset) {
      variant_id
      pos
      exome {
        ac
        an
        af
      }
      genome {
        ac
        an
        af
      }
    }
  }
}
"""


class GnomADClient(BaseAPIClient):
    """Client for gnomAD GraphQL API (https://gnomad.broadinstitute.org/api)."""

    BASE_URL = "https://gnomad.broadinstitute.org/api"
    DEFAULT_HEADERS = {
        "Content-Type": "application/json",
        "User-Agent": "pgx-mcp/0.1.0",
    }

    def __init__(self, settings: Settings) -> None:
        super().__init__(
            rate_limit=settings.gnomad_rate_limit,
            cache_ttl=settings.cache_ttl_seconds,
        )

    async def _graphql(self, query: str, variables: dict[str, Any]) -> Any:
        """Execute a GraphQL query against gnomAD."""
        return await self.post("", json={"query": query, "variables": variables})

    async def get_variant(
        self,
        variant_id: str,
        dataset: str = "gnomad_r4",
    ) -> dict[str, Any] | None:
        """Get variant details including population frequencies.

        Args:
            variant_id: gnomAD-style variant ID (e.g. '22-42126611-C-T').
            dataset: gnomAD dataset version.
        """
        data = await self._graphql(
            VARIANT_QUERY, {"variantId": variant_id, "dataset": dataset}
        )
        return data.get("data", {}).get("variant")

    async def get_gene_variants(
        self,
        gene_symbol: str,
        dataset: str = "gnomad_r4",
        reference_genome: str = "GRCh38",
    ) -> dict[str, Any] | None:
        """Get all variants in a gene with their frequencies."""
        data = await self._graphql(
            GENE_VARIANTS_QUERY,
            {
                "geneSymbol": gene_symbol,
                "dataset": dataset,
                "referenceGenome": reference_genome,
            },
        )
        return data.get("data", {}).get("gene")
