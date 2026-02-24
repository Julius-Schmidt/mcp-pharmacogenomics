"""Static reference resources for pharmacogenomics."""

from __future__ import annotations

from pgx_mcp.server import mcp

# Key pharmacogenes with CPIC guidelines and their associated drugs
CPIC_GENES: dict[str, str] = {
    "CYP2D6": "Codeine, Tramadol, Tamoxifen, Ondansetron, SSRIs, TCAs",
    "CYP2C19": "Clopidogrel, Voriconazole, PPIs, SSRIs, TCAs",
    "CYP2C9": "Warfarin, Phenytoin, NSAIDs",
    "CYP3A5": "Tacrolimus",
    "CYP2B6": "Efavirenz",
    "DPYD": "Fluoropyrimidines (5-FU, Capecitabine)",
    "TPMT": "Thiopurines (Azathioprine, 6-MP, Thioguanine)",
    "NUDT15": "Thiopurines (Azathioprine, 6-MP, Thioguanine)",
    "UGT1A1": "Irinotecan, Atazanavir",
    "VKORC1": "Warfarin",
    "SLCO1B1": "Simvastatin",
    "IFNL3": "Peginterferon alfa-2a/2b",
    "RYR1": "Volatile anesthetics, Succinylcholine",
    "CACNA1S": "Volatile anesthetics, Succinylcholine",
    "G6PD": "Rasburicase",
    "HLA-A": "Carbamazepine, Oxcarbazepine, Allopurinol",
    "HLA-B": "Abacavir, Carbamazepine, Phenytoin, Allopurinol",
    "MT-RNR1": "Aminoglycosides",
    "NAT2": "Hydralazine",
}


@mcp.resource("pgx://genes/cpic-list")
def get_cpic_gene_list() -> str:
    """List of all pharmacogenes with CPIC dosing guidelines and their associated drugs."""
    lines = ["# CPIC Pharmacogenes and Associated Drugs\n"]
    for gene, drugs in sorted(CPIC_GENES.items()):
        lines.append(f"- **{gene}**: {drugs}")
    lines.append(
        f"\n_Total: {len(CPIC_GENES)} genes with CPIC guidelines_\n"
        f"_Source: cpicpgx.org/guidelines/_"
    )
    return "\n".join(lines)


@mcp.resource("pgx://genes/{gene_symbol}")
def get_gene_reference(gene_symbol: str) -> str:
    """Quick reference for a specific pharmacogene with associated drugs and key links."""
    gene = gene_symbol.upper()
    drugs = CPIC_GENES.get(gene, "No CPIC guideline available for this gene")
    return (
        f"# {gene} — Pharmacogenomics Reference\n\n"
        f"**Associated Drugs (CPIC)**: {drugs}\n\n"
        f"**Key Links**:\n"
        f"- PharmGKB: https://www.pharmgkb.org/gene/{gene}\n"
        f"- CPIC: https://cpicpgx.org/genes-drugs/\n"
        f"- gnomAD: https://gnomad.broadinstitute.org/gene/{gene}\n"
        f"\n_Use the `pgx_consultation` tool for comprehensive "
        f"genotype-specific information._"
    )


@mcp.resource("pgx://about")
def get_about() -> str:
    """About pgx-mcp: server capabilities, data sources, and limitations."""
    return (
        "# pgx-mcp: Pharmacogenomics Knowledge Server\n\n"
        "## Data Sources\n"
        "- **PharmGKB**: Drug-gene interactions, clinical annotations, "
        "CPIC/DPWG guidelines\n"
        "- **ClinVar**: Variant clinical significance and pathogenicity\n"
        "- **gnomAD**: Population allele frequencies across ancestries\n"
        "- **Open Targets**: Drug-target-disease associations, "
        "pharmacogenomics evidence\n"
        "- **ClinicalTrials.gov**: US and international clinical trial search\n\n"
        "## Limitations\n"
        "- Data freshness depends on source API availability\n"
        "- EU Clinical Trials Register has no public API; European trials are "
        "covered through ClinicalTrials.gov registrations\n"
        "- Not a substitute for professional clinical judgment\n"
        "- gnomAD population frequency queries require variant IDs in "
        "positional format (chrom-pos-ref-alt)\n"
    )
