"""Drug-gene interaction tools."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from pgx_mcp.server import AppContext, mcp


@mcp.tool()
async def get_drug_gene_interactions(
    ctx: Context,
    drug: str,
    gene: str | None = None,
) -> str:
    """Get pharmacogenomic interactions between a drug and gene(s) from PharmGKB.

    Returns clinical annotations showing how genetic variants affect drug
    response, including evidence level, phenotype categories, and
    associated genotypes.

    Args:
        drug: Drug/chemical name (e.g. 'codeine', 'warfarin', 'clopidogrel')
        gene: Optional gene symbol to narrow results (e.g. 'CYP2D6')
    """
    app: AppContext = ctx.request_context.lifespan_context
    annotations = await app.pharmgkb.search_clinical_annotations(
        gene=gene, chemical=drug
    )

    if not annotations:
        qualifier = f" for gene {gene}" if gene else ""
        return f"No clinical annotations found for {drug}{qualifier} in PharmGKB."

    lines = [
        f"## PharmGKB Clinical Annotations for {drug}"
        + (f" / {gene}" if gene else "")
    ]
    for ann in annotations[:15]:
        ann_id = ann.get("id", "N/A")
        level_obj = ann.get("levelOfEvidence", {})
        level = level_obj.get("term", "N/A") if isinstance(level_obj, dict) else "N/A"
        genotype_display = ann.get("location", {}).get("displayName", "N/A")
        types = ann.get("types", [])
        lines.append(
            f"\n### Annotation {ann_id} (Level {level})\n"
            f"- **Genotypes**: {genotype_display}\n"
            f"- **Phenotype Categories**: "
            f"{', '.join(str(t) for t in types) if types else 'N/A'}"
        )
    return "\n".join(lines)


@mcp.tool()
async def get_drug_info(
    ctx: Context,
    drug: str,
) -> str:
    """Get comprehensive drug information from PharmGKB.

    Returns drug details including PharmGKB ID, generic/trade names,
    and cross-references.

    Args:
        drug: Drug name (e.g. 'codeine', 'warfarin', 'irinotecan')
    """
    app: AppContext = ctx.request_context.lifespan_context
    chemicals = await app.pharmgkb.search_chemicals(drug)

    if not chemicals:
        return f"No drug/chemical found matching '{drug}' in PharmGKB."

    chem = chemicals[0]
    chem_id = chem.get("id", "")
    detail = await app.pharmgkb.get_chemical(chem_id)

    name = detail.get("name", drug)
    pgkb_id = detail.get("id", "N/A")
    generic_names = detail.get("genericNames", [])
    trade_names = detail.get("tradeNames", [])
    drug_url = f"https://www.pharmgkb.org/chemical/{pgkb_id}"

    return (
        f"## {name}\n"
        f"- **PharmGKB ID**: {pgkb_id}\n"
        f"- **Generic Names**: "
        f"{', '.join(generic_names) if generic_names else 'N/A'}\n"
        f"- **Trade Names**: "
        f"{', '.join(trade_names[:5]) if trade_names else 'N/A'}\n"
        f"- **PharmGKB URL**: {drug_url}"
    )


@mcp.tool()
async def search_drug_targets(
    ctx: Context,
    drug_name: str,
) -> str:
    """Search Open Targets for drug mechanism of action, indications, and pharmacogenomics data.

    Uses the Open Targets Platform to find detailed drug-target relationships
    including pharmacogenomic evidence linking variants to drug response.

    Args:
        drug_name: Drug name to search for (e.g. 'codeine', 'imatinib')
    """
    app: AppContext = ctx.request_context.lifespan_context

    hits = await app.opentargets.search(drug_name, entity_types=["drug"])
    if not hits:
        return f"No drug found matching '{drug_name}' in Open Targets."

    chembl_id = hits[0].get("id", "")
    drug_detail = await app.opentargets.get_drug(chembl_id)
    if not drug_detail:
        return f"Could not retrieve details for {drug_name} ({chembl_id})."

    lines = [f"## {drug_detail.get('name', drug_name)} ({chembl_id})"]
    lines.append(f"- **Drug Type**: {drug_detail.get('drugType', 'N/A')}")

    # Mechanisms of action
    moas = drug_detail.get("mechanismsOfAction", {}).get("rows", [])
    if moas:
        lines.append("\n### Mechanisms of Action")
        for moa in moas:
            targets = [
                t.get("approvedSymbol", "") for t in moa.get("targets", [])
            ]
            lines.append(
                f"- {moa.get('mechanismOfAction', 'N/A')} "
                f"(targets: {', '.join(targets)})"
            )

    # PGx data
    pgx = drug_detail.get("pharmacogenomics", [])
    if pgx:
        lines.append(f"\n### Pharmacogenomics Evidence ({len(pgx)} record(s))")
        for p in pgx[:10]:
            lines.append(
                f"- **{p.get('variantRsId', 'N/A')}** | "
                f"Genotype: {p.get('genotype', 'N/A')} | "
                f"Phenotype: {p.get('phenotypeText', 'N/A')} | "
                f"Level: {p.get('evidenceLevel', 'N/A')}"
            )

    return "\n".join(lines)
