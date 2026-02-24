"""Configuration management via environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Server settings loaded from environment variables with PGX_MCP_ prefix."""

    # NCBI/ClinVar (optional — increases rate limit from 3/s to 10/s)
    ncbi_api_key: str | None = None

    # Cache TTL in seconds (default: 1 hour for relatively static data)
    cache_ttl_seconds: int = 3600

    # Rate limiting defaults (requests per second)
    pharmgkb_rate_limit: float = 1.5  # PharmGKB limit: 2/s
    clinvar_rate_limit: float = 2.5  # ClinVar: 3/s without key, 9/s with
    gnomad_rate_limit: float = 2.0  # gnomAD: conservative to avoid IP block
    opentargets_rate_limit: float = 5.0  # OpenTargets: no published limit
    clinical_trials_rate_limit: float = 0.7  # CT.gov: ~50/min

    model_config = {"env_prefix": "PGX_MCP_"}
