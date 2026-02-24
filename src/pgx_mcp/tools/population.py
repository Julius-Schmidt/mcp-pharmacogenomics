"""Population allele frequency tools."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from pgx_mcp.server import AppContext, mcp


@mcp.tool()
async def get_variant_frequency(
    ctx: Context,
    variant_id: str,
    dataset: str = "gnomad_r4",
) -> str:
    """Get population allele frequencies for a genetic variant from gnomAD.

    Returns allele frequency data across global populations (African,
    European, East Asian, South Asian, Latino, etc.) from both exome
    and genome sequencing data.

    Args:
        variant_id: Variant in gnomAD format (e.g. '22-42126611-C-T')
                    or positional format chrom-pos-ref-alt
        dataset: gnomAD dataset (default 'gnomad_r4'; options: gnomad_r4,
                 gnomad_r3, gnomad_r2_1)
    """
    app: AppContext = ctx.request_context.lifespan_context
    variant = await app.gnomad.get_variant(variant_id, dataset)

    if not variant:
        return (
            f"Variant '{variant_id}' not found in gnomAD ({dataset}). "
            f"Ensure the variant ID is in gnomAD format (chrom-pos-ref-alt) "
            f"or try a different dataset."
        )

    lines = [f"## gnomAD Frequencies: {variant.get('variant_id', variant_id)}"]
    lines.append(
        f"- **Genome Build**: {variant.get('reference_genome', 'N/A')}"
    )
    lines.append(
        f"- **Position**: chr{variant.get('chrom', '?')}:{variant.get('pos', '?')}"
    )

    for source_name, source_key in [("Exome", "exome"), ("Genome", "genome")]:
        source_data = variant.get(source_key)
        if not source_data:
            continue
        ac = source_data.get("ac", 0)
        an = source_data.get("an", 0)
        af = source_data.get("af", 0)
        lines.append(f"\n### {source_name} Data")
        lines.append(f"- **Global AF**: {af:.6f} (AC={ac}, AN={an})")

        populations = source_data.get("populations", [])
        if populations:
            lines.append("- **Population frequencies**:")
            for pop in populations:
                pop_id = pop.get("id", "?")
                pop_ac = pop.get("ac", 0)
                pop_an = pop.get("an", 0)
                pop_af = pop_ac / pop_an if pop_an > 0 else 0
                lines.append(
                    f"  - {pop_id}: AF={pop_af:.6f} (AC={pop_ac}, AN={pop_an})"
                )

    return "\n".join(lines)
