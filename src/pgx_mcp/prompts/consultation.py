"""Pharmacogenomics consultation prompts."""

from __future__ import annotations

from pgx_mcp.server import mcp


@mcp.prompt()
def pgx_patient_consult(
    gene: str,
    diplotype: str,
    drug: str = "",
    clinical_scenario: str = "",
) -> str:
    """Generate a pharmacogenomics consultation for a patient genotype.

    Guides Claude through a systematic PGx evaluation using available tools.

    Args:
        gene: The pharmacogene (e.g. 'CYP2D6')
        diplotype: Patient's diplotype (e.g. '*4/*4')
        drug: Optional drug being considered
        clinical_scenario: Optional clinical context
    """
    drug_text = f" being considered for {drug}" if drug else ""
    scenario_text = (
        f"\nClinical scenario: {clinical_scenario}" if clinical_scenario else ""
    )

    return (
        f"A patient has been genotyped as {gene} {diplotype}{drug_text}."
        f"{scenario_text}\n\n"
        f"Please perform a comprehensive pharmacogenomics consultation by:\n\n"
        f"1. First, use the `pgx_consultation` tool with gene='{gene}', "
        f"diplotype='{diplotype}'"
        + (f", drug='{drug}'" if drug else "")
        + " to get a comprehensive overview.\n\n"
        "2. Based on the results, interpret:\n"
        "   - What metabolizer phenotype does this diplotype correspond to?\n"
        "   - What is the clinical significance of the identified alleles?\n"
        "   - What dosing adjustments are recommended by CPIC/DPWG guidelines?\n"
        "   - How common is this genotype across different populations?\n"
        "   - Are there any active clinical trials relevant to this genotype?\n\n"
        "3. Provide a clear clinical recommendation with:\n"
        "   - Metabolizer phenotype classification\n"
        "   - Specific dosing guidance if applicable\n"
        "   - Alternative drug recommendations if the current drug is "
        "contraindicated\n"
        "   - Any important safety warnings\n\n"
        "4. Note any limitations or uncertainties in the available evidence.\n\n"
        "Format the response clearly for a clinician audience."
    )


@mcp.prompt()
def variant_interpretation(variant: str) -> str:
    """Interpret a genetic variant using multiple data sources.

    Args:
        variant: Variant identifier (rsID, HGVS, or gene*allele)
    """
    return (
        f"Please interpret the genetic variant '{variant}' by:\n\n"
        f"1. Use `lookup_variant_clinvar` to check clinical significance "
        f"in ClinVar\n"
        f"2. Use `get_drug_gene_interactions` with the associated gene to "
        f"find pharmacogenomic implications\n"
        f"3. Use `get_variant_frequency` to check population frequencies "
        f"in gnomAD (if a positional ID is available)\n\n"
        f"Synthesize the results into a clear interpretation covering:\n"
        f"- Pathogenicity classification\n"
        f"- Known drug-gene interactions\n"
        f"- Population frequency context\n"
        f"- Clinical actionability"
    )


@mcp.prompt()
def drug_pgx_review(drug: str) -> str:
    """Review all pharmacogenomic considerations for a drug.

    Args:
        drug: Drug name to review
    """
    return (
        f"Please review all pharmacogenomic considerations for '{drug}' by:\n\n"
        f"1. Use `get_drug_info` to get drug details from PharmGKB\n"
        f"2. Use `get_drug_gene_interactions` with drug='{drug}' to find "
        f"all gene-drug interactions\n"
        f"3. Use `search_drug_targets` to get mechanism of action and PGx "
        f"evidence from Open Targets\n"
        f"4. For each gene found, use `get_dosing_guideline` to check for "
        f"CPIC/DPWG guidelines\n\n"
        f"Provide a comprehensive summary of:\n"
        f"- All genes that affect response to {drug}\n"
        f"- CPIC/DPWG guideline recommendations for each gene-drug pair\n"
        f"- Level of evidence for each interaction\n"
        f"- Key genotypes to test before prescribing"
    )
