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
