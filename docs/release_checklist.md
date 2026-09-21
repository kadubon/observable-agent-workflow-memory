# Release Checklist

Before publishing a release:

- Run `uv sync --extra dev`.
- Run `uv run pytest`.
- Run `uv run ruff check .`.
- Run `uv run mypy src`.
- Run the local examples that do not require network access.
- Build with `uv build` and inspect the sdist/wheel contents.
- Confirm no secrets, local paths, `.env`, SQLite state, or virtualenv files are
  included.
- Confirm README limitations still avoid truth-certification claims.
- Confirm `SECURITY.md` and `docs/security_model.md` are consistent.
- Tag the release.
- Create the GitHub release.
- Optionally publish to PyPI.
- Optionally archive the release to Zenodo.

## 0.2.0b0 receiver profile

For 0.2.0b0, PyPI, TestPyPI, Zenodo and deployment are NOT_REQUESTED. Inspect all tag/release triggers. Run uv sync --extra dev --group integration --locked, the full pytest coverage matrix, Ruff, strict mypy, scripts/coverage_gate.py, scripts/schemas.py --check, scripts/selected_faults.py, pip-audit and scripts/public_audit.py. Build exact merged-commit artifacts once, qualify base/native installs outside checkout, publish a GitHub prerelease, then download public assets unauthenticated and repeat wheel/sdist installs with caches disabled. Record actual hashes/runs/results in publication-0.2.0b0.md without replacing assets.
