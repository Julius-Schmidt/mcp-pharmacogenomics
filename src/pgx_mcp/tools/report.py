"""Composite pharmacogenomics consultation tool."""

from __future__ import annotations

import logging

from mcp.server.fastmcp import Context

from pgx_mcp.server import AppContext, mcp

logger = logging.getLogger(__name__)


def _parse_alleles(diplotype: str) -> list[str]:
    """Parse a diplotype string like '*1/*4' into individual alleles ['*1', '*4']."""
    return [a.strip() for a in diplotype.split("/") if a.strip()]


@mcp.tool()
async def pgx_consultation(
    ctx: Context,
    gene: str,
    diplotype: str,
    drug: str | None = None,
    clinical_context: str | None = None,
) -> str:
    """Run a comprehensive pharmacogenomics consultation for a patient genotype.

    This is the primary high-level tool for pharmacogenomics queries. Given a
    gene and diplotype (e.g. CYP2D6 *4/*4), it aggregates data from multiple
    sources to produce a comprehensive clinical summary:

    1. Gene information from PharmGKB
    2. Drug-gene clinical annotations from PharmGKB
    3. CPIC/DPWG dosing guidelines from PharmGKB
    4. Variant clinical significance from ClinVar
    5. Active pharmacogenomics clinical trials

    Args:
        gene: Gene symbol (e.g. 'CYP2D6', 'CYP2C19', 'DPYD', 'TPMT', 'VKORC1')
        diplotype: Patient diplotype (e.g. '*1/*4', '*2/*2', '*4/*4')
        drug: Optional specific drug to focus on (e.g. 'codeine', 'warfarin')
        clinical_context: Optional clinical context (e.g. 'pain management',
                          'anticoagulation therapy', 'cancer chemotherapy')
    """
    app: AppContext = ctx.request_context.lifespan_context
    sections: list[str] = []
    sections.append(
        f"# Pharmacogenomics Consultation: {gene} {diplotype}"
        + (f" ({drug})" if drug else "")
    )

    if clinical_context:
        sections.append(f"**Clinical Context**: {clinical_context}\n")

    # 1. Gene information from PharmGKB
    try:
        gene_info = await app.pharmgkb.get_gene(gene)
        if gene_info:
            sections.append(
                f"## Gene: {gene}\n"
                f"- **PharmGKB ID**: {gene_info.get('id', 'N/A')}\n"
                f"- **PharmGKB URL**: "
                f"https://www.pharmgkb.org/gene/{gene_info.get('id', '')}"
            )
    except Exception:
        logger.debug("Could not retrieve gene details for %s", gene, exc_info=True)
        sections.append(f"## Gene: {gene}\n- _(Could not retrieve gene details)_")

    # 2. Clinical annotations (drug-gene interactions)
    try:
        annotations = await app.pharmgkb.search_clinical_annotations(
            gene=gene, chemical=drug
        )
        if annotations:
            sections.append(
                f"\n## Clinical Annotations ({len(annotations)} found)"
            )
            for ann in annotations[:10]:
                level_obj = ann.get("levelOfEvidence", {})
                level = (
                    level_obj.get("term", "N/A")
                    if isinstance(level_obj, dict)
                    else "N/A"
                )
                genotype_display = ann.get("location", {}).get(
                    "displayName", "N/A"
                )
                types = ann.get("types", [])
                sections.append(
                    f"- **Level {level}**: "
                    f"Genotypes: {genotype_display} | "
                    f"Categories: {', '.join(str(t) for t in types)}"
                )
        else:
            sections.append(
                "\n## Clinical Annotations\n"
                "- None found for this gene-drug pair."
            )
    except Exception:
        logger.debug("Error retrieving annotations", exc_info=True)
        sections.append(
            "\n## Clinical Annotations\n- _(Error retrieving annotations)_"
        )

    # 3. Dosing guidelines
    if drug:
        try:
            guidelines = await app.pharmgkb.search_guideline_annotations(
                gene=gene, chemical=drug
            )
            if guidelines:
                sections.append("\n## Dosing Guidelines")
                for g in guidelines:
                    name = g.get("name", "Unnamed")
                    g_id = g.get("id", "")
                    sections.append(
                        f"- **{name}**: "
                        f"https://www.pharmgkb.org/guidelineAnnotation/{g_id}"
                    )
                    full = await app.pharmgkb.get_guideline_annotation(g_id)
                    summary_obj = (full or {}).get("summaryMarkdown", "")
                    if isinstance(summary_obj, dict):
                        summary = summary_obj.get("html", "")
                    else:
                        summary = summary_obj or ""
                    if summary:
                        sections.append(f"  {summary[:1500]}")
            else:
                sections.append(
                    f"\n## Dosing Guidelines\n"
                    f"- No CPIC/DPWG guideline found for {gene}/{drug}."
                )
        except Exception:
            logger.debug("Error retrieving guidelines", exc_info=True)
            sections.append(
                "\n## Dosing Guidelines\n- _(Error retrieving guidelines)_"
            )

    # 4. ClinVar significance for the alleles
    for allele in _parse_alleles(diplotype):
        try:
            query = f"{gene}{allele}" if "*" in allele else allele
            clinvar_results = await app.clinvar.lookup_variant(query)
            if clinvar_results:
                sig = (
                    clinvar_results[0]
                    .get("clinical_significance", {})
                    .get("description", "N/A")
                )
                sections.append(
                    f"\n## ClinVar: {gene} {allele}\n"
                    f"- **Significance**: {sig}"
                )
        except Exception:
            logger.debug(
                "Error looking up allele %s in ClinVar", allele, exc_info=True
            )

    # 5. Active clinical trials
    try:
        trial_query = f"pharmacogenomics {gene}"
        if drug:
            trial_query += f" {drug}"
        trial_data = await app.clinical_trials.search_studies(
            condition=trial_query,
            status=["RECRUITING", "NOT_YET_RECRUITING"],
            page_size=5,
        )
        trials = trial_data.get("studies", [])
        if trials:
            sections.append(
                f"\n## Active Clinical Trials ({len(trials)} found)"
            )
            for t in trials:
                p = t.get("protocolSection", {})
                nct = p.get("identificationModule", {}).get("nctId", "")
                title = p.get("identificationModule", {}).get("briefTitle", "")
                sections.append(
                    f"- [{nct}](https://clinicaltrials.gov/study/{nct}): "
                    f"{title}"
                )
    except Exception:
        logger.debug("Error searching clinical trials", exc_info=True)

    sections.append(
        "\n---\n*Disclaimer: This information is for research and clinical "
        "decision support only. Always verify with primary sources and apply "
        "clinical judgment.*"
    )
    return "\n".join(sections)
