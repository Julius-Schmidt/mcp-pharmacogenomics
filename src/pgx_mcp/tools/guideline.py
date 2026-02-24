"""CPIC and DPWG guideline tools."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from pgx_mcp.server import AppContext, mcp


@mcp.tool()
async def get_dosing_guideline(
    ctx: Context,
    gene: str,
    drug: str,
) -> str:
    """Get CPIC or DPWG pharmacogenomic dosing guidelines for a gene-drug pair.

    Returns evidence-based dosing recommendations based on genotype/phenotype,
    including recommendation strength and the source guideline.

    This is the primary tool for answering questions like: "What dose of
    codeine should I prescribe for a CYP2D6 poor metabolizer?"

    Args:
        gene: Gene symbol (e.g. 'CYP2D6', 'CYP2C19', 'DPYD', 'TPMT')
        drug: Drug name (e.g. 'codeine', 'clopidogrel', 'fluorouracil')
    """
    app: AppContext = ctx.request_context.lifespan_context
    guidelines = await app.pharmgkb.search_guideline_annotations(
        gene=gene, chemical=drug
    )

    if not guidelines:
        return (
            f"No CPIC/DPWG dosing guidelines found for {gene}/{drug}. "
            f"This gene-drug pair may not yet have a published guideline."
        )

    sections: list[str] = [f"## Dosing Guidelines: {gene} / {drug}\n"]
    for g in guidelines:
        g_id = g.get("id", "N/A")
        name = g.get("name", "Unnamed guideline")
        sections.append(
            f"### {name}\n"
            f"- **PharmGKB ID**: {g_id}\n"
            f"- **URL**: https://www.pharmgkb.org/guidelineAnnotation/{g_id}"
        )

        full = await app.pharmgkb.get_guideline_annotation(g_id)
        if full:
            summary_obj = full.get("summaryMarkdown", full.get("summary", ""))
            if isinstance(summary_obj, dict):
                summary = summary_obj.get("html", "")
            else:
                summary = summary_obj or ""
            if summary:
                sections.append(f"\n**Summary**:\n{summary[:2000]}")

    return "\n\n".join(sections)
