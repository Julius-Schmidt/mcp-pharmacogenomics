"""Variant lookup and clinical significance tools."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from pgx_mcp.server import AppContext, mcp


@mcp.tool()
async def lookup_variant_clinvar(
    ctx: Context,
    variant: str,
) -> str:
    """Look up a genetic variant in ClinVar to get clinical significance.

    Searches ClinVar for a variant by name (rsID like 'rs3892097',
    star allele like 'CYP2D6*4', or HGVS notation) and returns
    clinical significance, associated conditions, and review status.

    Args:
        variant: Variant identifier (rsID, gene*allele, or HGVS notation)
    """
    app: AppContext = ctx.request_context.lifespan_context
    results = await app.clinvar.lookup_variant(variant)

    if not results:
        return f"No ClinVar records found for variant '{variant}'."

    lines: list[str] = []
    for r in results:
        title = r.get("title", "Unknown")
        significance = r.get("clinical_significance", {}).get(
            "description", "Not provided"
        )
        review_status = r.get("clinical_significance", {}).get(
            "review_status", "Unknown"
        )
        conditions = (
            ", ".join(t.get("trait_name", "") for t in r.get("trait_set", []))
            or "None listed"
        )
        lines.append(
            f"## {title}\n"
            f"- **Clinical Significance**: {significance}\n"
            f"- **Review Status**: {review_status}\n"
            f"- **Conditions**: {conditions}\n"
            f"- **ClinVar ID**: {r.get('uid', 'N/A')}"
        )
    return "\n\n---\n\n".join(lines)


@mcp.tool()
async def search_gene_variants_clinvar(
    ctx: Context,
    gene: str,
    significance: str | None = None,
    max_results: int = 10,
) -> str:
    """Search ClinVar for variants in a specific gene, optionally filtered by clinical significance.

    Args:
        gene: Gene symbol (e.g. 'CYP2D6', 'CYP2C19', 'DPYD')
        significance: Optional filter: 'pathogenic', 'likely_pathogenic',
                      'benign', 'likely_benign', 'uncertain_significance'
        max_results: Maximum number of results (default 10, max 50)
    """
    app: AppContext = ctx.request_context.lifespan_context
    max_results = min(max_results, 50)
    uids = await app.clinvar.search_variants(gene, significance, max_results)

    if not uids:
        filter_text = f" with significance '{significance}'" if significance else ""
        return f"No ClinVar variants found for gene {gene}{filter_text}."

    summaries = await app.clinvar.get_variant_summaries(uids)
    lines = [f"Found {len(summaries)} ClinVar variant(s) for gene {gene}:\n"]
    for s in summaries:
        title = s.get("title", "Unknown")
        sig = s.get("clinical_significance", {}).get("description", "N/A")
        lines.append(f"- **{title}**: {sig}")
    return "\n".join(lines)
