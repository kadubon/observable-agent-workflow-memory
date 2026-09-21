"""Inspect distribution contents and bind one build to its source commit."""

import hashlib
import json
import os
import subprocess
import tarfile
import zipfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
dist = root / "dist"
artifacts = sorted([*dist.glob("*.whl"), *dist.glob("*.tar.gz")])
assert len(artifacts) == 2
for artifact in artifacts:
    if artifact.suffix == ".whl":
        with zipfile.ZipFile(artifact) as archive:
            names = archive.namelist()
    else:
        with tarfile.open(artifact) as archive:
            names = archive.getnames()
    assert any(name.endswith("qualified/native.py") for name in names)
    for suffix in (
        "Qualification.schema.json",
        "003_receiver_events.sql",
        "qualified/resources/manifest.json",
        "certified_workflow_memory.py",
    ):
        assert any(name.endswith(suffix) for name in names), suffix
    assert not any(
        Path(name).is_absolute()
        or ".." in Path(name).parts
        or any(part in {".git", ".venv", ".hypothesis", "__pycache__"} for part in Path(name).parts)
        or name.endswith((".sqlite", ".db", ".env"))
        for name in names
    )
hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts}
manifest = {
    "package": "observable-agent-workflow-memory",
    "version": "0.2.0b0",
    "classification": "Beta",
    "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
    "source_dirty": bool(
        subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()
    ),
    "workflow_run": os.getenv("GITHUB_RUN_ID"),
    "artifacts": hashes,
    "core_schema": "1.1",
    "profile_schema": "oawm_receiver_v1",
    "status": "build record; installation gates separate",
    "companions": {"ALT": "0.5.0", "CCR": "1.8.0"},
    "pypi": "NOT_REQUESTED",
    "attestation": None,
}
path = dist / "build-manifest.json"
path.write_text(json.dumps(manifest, indent=2) + "\n", newline="\n")
(dist / "SHA256SUMS").write_text(
    "".join(
        f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}\n" for p in [*artifacts, path]
    ),
    newline="\n",
)
print(json.dumps(manifest, indent=2))
