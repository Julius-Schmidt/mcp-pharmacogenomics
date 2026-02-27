# Contributing to pgx-mcp

Thanks for your interest in contributing to pgx-mcp!

## Reporting Issues

- Use [GitHub Issues](https://github.com/Julius-Schmidt/mcp-pharmacogenomics/issues) to report bugs or request features.
- Include steps to reproduce the issue, expected vs. actual behavior, and your Python version.

## Development Setup

```bash
git clone https://github.com/Julius-Schmidt/mcp-pharmacogenomics.git
cd mcp-pharmacogenomics
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest                                    # run all tests
pytest --cov=pgx_mcp --cov-report=term   # with coverage
ruff check src/ tests/                    # lint
mypy src/pgx_mcp/                         # type check
```

## Pull Requests

1. Fork the repository and create a branch from `main`.
2. Add tests for any new functionality.
3. Ensure all tests pass and linting is clean before submitting.
4. Keep PRs focused on a single change.

## Adding a New API Client

If you want to integrate a new database:

1. Create a client in `src/pgx_mcp/clients/` inheriting from `BaseAPIClient`.
2. Add the client to the `AppContext` in `server.py` and initialize it in `app_lifespan`.
3. Create tool functions in `src/pgx_mcp/tools/`.
4. Add test fixtures in `tests/fixtures/` and tests in `tests/test_clients/` and `tests/test_tools/`.

## Code Style

- Python 3.11+
- Formatted and linted with [ruff](https://docs.astral.sh/ruff/)
- Type-annotated (checked with mypy in strict mode)
