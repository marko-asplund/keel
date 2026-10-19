# Project instructions

## After making changes

Run these checks before considering work done:

```bash
uv run ruff check          # lint
uv run ruff format --check . # formatting
uv run basedpyright        # type check
uv run pytest --cov -v     # tests with coverage
```

All four must pass with zero warnings and 95%+ coverage.