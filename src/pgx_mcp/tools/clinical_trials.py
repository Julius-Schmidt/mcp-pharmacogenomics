"""Clinical trial search tools."""

from __future__ import annotations

from mcp.server.fastmcp import Context

from pgx_mcp.server import AppContext, mcp


@mcp.tool()
async def search_clinical_trials(
    ctx: Context,
    condition: str | None = None,
    intervention: str | None = None,
    location: str | None = None,
    status: str | None = None,
    phase: str | None = None,
    max_results: int = 10,
) -> str:
    """Search for clinical trials on ClinicalTrials.gov.

    Searches both US and international trials (including European trials
    registered at ClinicalTrials.gov). Covers pharmacogenomics-relevant
    trials for drug-gene interactions, biomarker studies, and precision
    medicine approaches.

    Args:
        condition: Disease or condition (e.g. 'breast cancer', 'pharmacogenomics CYP2D6')
        intervention: Drug or treatment (e.g. 'tamoxifen', 'gene therapy')
        location: Geographic location filter (e.g. 'Europe', 'Germany', 'United Kingdom')
        status: Comma-separated trial statuses (RECRUITING, COMPLETED, NOT_YET_RECRUITING, etc.)
        phase: Comma-separated phases (PHASE1, PHASE2, PHASE3, PHASE4)
        max_results: Number of results to return (default 10, max 50)
    """
    app: AppContext = ctx.request_context.lifespan_context
    max_results = min(max_results, 50)

    status_list = [s.strip() for s in status.split(",")] if status else None
    phase_list = [p.strip() for p in phase.split(",")] if phase else None

    data = await app.clinical_trials.search_studies(
        condition=condition,
        intervention=intervention,
        location=location,
        status=status_list,
        phase=phase_list,
        page_size=max_results,
    )

    studies = data.get("studies", [])
    total = data.get("totalCount", 0)

    if not studies:
        return "No clinical trials found matching your criteria."

    lines = [f"## Clinical Trials (showing {len(studies)} of {total} total)\n"]
    for study in studies:
        protocol = study.get("protocolSection", {})
        ident = protocol.get("identificationModule", {})
        status_mod = protocol.get("statusModule", {})
        design = protocol.get("designModule", {})
        desc = protocol.get("descriptionModule", {})

        nct_id = ident.get("nctId", "N/A")
        title = ident.get("briefTitle", "Untitled")
        overall_status = status_mod.get("overallStatus", "N/A")
        phases = (
            ", ".join(design.get("phases", [])) if design.get("phases") else "N/A"
        )
        brief_summary = desc.get("briefSummary", "")[:300]

        lines.append(
            f"### {nct_id}: {title}\n"
            f"- **Status**: {overall_status}\n"
            f"- **Phase**: {phases}\n"
            f"- **Summary**: {brief_summary}...\n"
            f"- **URL**: https://clinicaltrials.gov/study/{nct_id}\n"
        )

    return "\n".join(lines)


@mcp.tool()
async def get_trial_details(
    ctx: Context,
    nct_id: str,
) -> str:
    """Get full details for a specific clinical trial by NCT ID.

    Args:
        nct_id: ClinicalTrials.gov identifier (e.g. 'NCT04267848')
    """
    app: AppContext = ctx.request_context.lifespan_context
    study = await app.clinical_trials.get_study(nct_id)

    protocol = study.get("protocolSection", {})
    ident = protocol.get("identificationModule", {})
    status_mod = protocol.get("statusModule", {})
    desc = protocol.get("descriptionModule", {})
    eligibility = protocol.get("eligibilityModule", {})
    contacts = protocol.get("contactsLocationsModule", {})
    arms_interventions = protocol.get("armsInterventionsModule", {})

    title = ident.get("officialTitle", ident.get("briefTitle", "Untitled"))

    locations = contacts.get("locations", [])
    location_text = (
        "; ".join(
            f"{loc.get('facility', 'N/A')} "
            f"({loc.get('city', '')}, {loc.get('country', '')})"
            for loc in locations[:5]
        )
        or "Not listed"
    )

    interventions = arms_interventions.get("interventions", [])
    intervention_text = (
        "; ".join(
            f"{i.get('name', '')} ({i.get('type', '')})" for i in interventions
        )
        or "Not listed"
    )

    return (
        f"## {nct_id}: {title}\n\n"
        f"**Status**: {status_mod.get('overallStatus', 'N/A')}\n"
        f"**Description**: "
        f"{desc.get('detailedDescription', desc.get('briefSummary', 'N/A'))}\n\n"
        f"**Interventions**: {intervention_text}\n"
        f"**Eligibility**: "
        f"{eligibility.get('eligibilityCriteria', 'N/A')[:1000]}\n"
        f"**Locations**: {location_text}\n"
        f"**URL**: https://clinicaltrials.gov/study/{nct_id}"
    )
