# pgx-mcp

[![CI](https://github.com/Julius-Schmidt/mcp-pharmacogenomics/actions/workflows/ci.yml/badge.svg)](https://github.com/Julius-Schmidt/mcp-pharmacogenomics/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/pgx-mcp)](https://pypi.org/project/pgx-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/pgx-mcp)](https://pypi.org/project/pgx-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An open-source MCP server that gives Claude real-time access to pharmacogenomics databases — turning genetic variant lookups and drug interaction checks from a 45-minute manual workflow into a single conversation.

<!-- TODO: Add demo GIF/video here -->
<!-- ![Demo](assets/demo.gif) -->

## Features

- **ClinVar**: Variant clinical significance and pathogenicity
- **PharmGKB**: Drug-gene interactions, clinical annotations, CPIC/DPWG dosing guidelines
- **gnomAD**: Population allele frequencies across ancestries
- **Open Targets**: Drug-target-disease associations, pharmacogenomics evidence
- **ClinicalTrials.gov**: Clinical trial search (US and international)

## Installation

```bash
pip install pgx-mcp
```

Or with uvx:

```bash
uvx pgx-mcp
```

## Claude Desktop Configuration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "pgx-mcp": {
      "command": "uvx",
      "args": ["pgx-mcp"]
    }
  }
}
```

For local development:

```json
{
  "mcpServers": {
    "pgx-mcp": {
      "command": "uv",
      "args": ["--directory", "/path/to/mcp-pharmacogenomics", "run", "pgx-mcp"]
    }
  }
}
```

## Available Tools

| Tool | Source | Description |
|------|--------|-------------|
| `lookup_variant_clinvar` | ClinVar | Variant clinical significance |
| `search_gene_variants_clinvar` | ClinVar | List variants in a gene |
| `get_drug_gene_interactions` | PharmGKB | Clinical annotations for drug-gene pairs |
| `get_drug_info` | PharmGKB | Drug details and cross-references |
| `get_dosing_guideline` | PharmGKB | CPIC/DPWG dosing recommendations |
| `search_drug_targets` | Open Targets | Drug mechanisms, indications, PGx evidence |
| `get_variant_frequency` | gnomAD | Population allele frequencies |
| `search_clinical_trials` | ClinicalTrials.gov | Trial search with filters |
| `get_trial_details` | ClinicalTrials.gov | Full trial details |
| `pgx_consultation` | All | Comprehensive PGx consultation report |

## Example Usage

Ask Claude:

> "My patient is a CYP2D6 poor metabolizer (*4/*4) and needs pain management. What should I prescribe?"

> "What are the CPIC guidelines for clopidogrel and CYP2C19?"

> "Are there any recruiting pharmacogenomics clinical trials in Germany?"

## Configuration

All settings are optional and configured via environment variables (or a `.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `PGX_MCP_NCBI_API_KEY` | None | NCBI API key for higher ClinVar rate limits (3/s → 9/s) |
| `PGX_MCP_CACHE_TTL_SECONDS` | 3600 | Cache duration in seconds |

## Development

```bash
git clone https://github.com/Julius-Schmidt/mcp-pharmacogenomics.git
cd mcp-pharmacogenomics
pip install -e ".[dev]"
pytest
```

## Roadmap

- [ ] Demo video/GIF in README
- [ ] EU Clinical Trials Register integration (currently no public API — European trials are covered through ClinicalTrials.gov registrations)
- [ ] PharmVar star-allele nomenclature lookups
- [ ] FDA Pharmacogenomic Biomarkers table integration

## License

MIT
