"""pgx-mcp: Pharmacogenomics MCP server."""

from __future__ import annotations

import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP

from pgx_mcp.clients.clinical_trials import ClinicalTrialsClient
from pgx_mcp.clients.clinvar import ClinVarClient
from pgx_mcp.clients.gnomad import GnomADClient
from pgx_mcp.clients.opentargets import OpenTargetsClient
from pgx_mcp.clients.pharmgkb import PharmGKBClient
from pgx_mcp.config import Settings

# Logging to stderr (required for stdio transport — stdout is for JSON-RPC)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("pgx-mcp")


@dataclass
class AppContext:
    """Holds initialized API clients for the server lifespan."""

    pharmgkb: PharmGKBClient
    clinvar: ClinVarClient
    gnomad: GnomADClient
    opentargets: OpenTargetsClient
    clinical_trials: ClinicalTrialsClient


@asynccontextmanager
async def app_lifespan(server: FastMCP[AppContext]) -> AsyncIterator[AppContext]:
    """Initialize and tear down API clients."""
    settings = Settings()
    pharmgkb = PharmGKBClient(settings)
    clinvar = ClinVarClient(settings)
    gnomad = GnomADClient(settings)
    opentargets = OpenTargetsClient(settings)
    clinical_trials = ClinicalTrialsClient(settings)

    try:
        await pharmgkb.start()
        await clinvar.start()
        await gnomad.start()
        await opentargets.start()
        await clinical_trials.start()
        logger.info("All API clients initialized")
        yield AppContext(
            pharmgkb=pharmgkb,
            clinvar=clinvar,
            gnomad=gnomad,
            opentargets=opentargets,
            clinical_trials=clinical_trials,
        )
    finally:
        await pharmgkb.close()
        await clinvar.close()
        await gnomad.close()
        await opentargets.close()
        await clinical_trials.close()
        logger.info("All API clients closed")


mcp = FastMCP[AppContext](
    "pgx-mcp",
    instructions=(
        "Pharmacogenomics knowledge server providing real-time access to "
        "ClinVar, PharmGKB, gnomAD, OpenTargets, and ClinicalTrials.gov. "
        "Use the pgx_consultation tool for comprehensive genotype-based "
        "clinical recommendations, or individual tools for targeted queries."
    ),
    lifespan=app_lifespan,
)

# Import tool/resource/prompt modules to register them with the mcp instance.
# These modules use @mcp.tool(), @mcp.resource(), @mcp.prompt() decorators.
import pgx_mcp.prompts.consultation  # noqa: E402, F401
import pgx_mcp.resources.references  # noqa: E402, F401
import pgx_mcp.tools.clinical_trials  # noqa: E402, F401
import pgx_mcp.tools.drug  # noqa: E402, F401
import pgx_mcp.tools.guideline  # noqa: E402, F401
import pgx_mcp.tools.population  # noqa: E402, F401
import pgx_mcp.tools.report  # noqa: E402, F401
import pgx_mcp.tools.variant  # noqa: E402, F401


def main() -> None:
    """Entry point for the pgx-mcp command."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    # Workaround for the python -m double-import problem:
    # This file runs as __main__, but tool modules import pgx_mcp.server,
    # causing a second copy. Tools register on pgx_mcp.server.mcp, not
    # __main__.mcp. We must run the instance that has the tools.
    import pgx_mcp.server as _self

    _self.main()
