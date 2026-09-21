"""Cache-disabled fresh base and native installations of exact downloaded bytes."""

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("dist", type=Path)
parser.add_argument("--python", default="3.13")
parser.add_argument("--sdist", action="store_true")
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
dist = args.dist.resolve()
manifest = json.loads((dist / "build-manifest.json").read_text())
for name, expected in manifest["artifacts"].items():
    assert hashlib.sha256((dist / name).read_bytes()).hexdigest() == expected
artifact = next(dist.glob("*.tar.gz" if args.sdist else "*.whl"))
probe = Path(__file__).with_name("installed_probe.py").resolve()
reports = []
for native in (False, True):
    scratch = Path(tempfile.mkdtemp(prefix="oawm-installed-"))
    env = scratch / "env"
    subprocess.run(["uv", "--no-cache", "venv", "--python", args.python, str(env)], check=True)
    python = env / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    packages = [str(artifact), "pip>=26.2.1"]
    if native:
        packages += [
            "https://github.com/kadubon/alt-foundry-kernel/releases/download/v0.5.0/alt_foundry_kernel-0.5.0-py3-none-any.whl#sha256=cd6755db6d97f978300d978695dc70c19d64fdd11c58e0c6dc4c1fcb7db9f487",
            "https://github.com/kadubon/collective-capability-runtime/releases/download/v1.8.0/collective_capability_runtime-1.8.0-py3-none-any.whl#sha256=97b2f3dc1f675c78246c362d211b71452b721b001e25dd2711263f34874f8b25",
        ]
    subprocess.run(
        [
            "uv",
            "--no-cache",
            "pip",
            "install",
            "--python",
            str(python),
            "--index-url",
            "https://pypi.org/simple",
            *packages,
        ],
        cwd=scratch,
        check=True,
    )
    subprocess.run([str(python), "-I", "-m", "pip", "check"], cwd=scratch, check=True)
    command = env / ("Scripts/oawm.exe" if os.name == "nt" else "bin/oawm")
    subprocess.run([str(command), "--help"], cwd=scratch, check=True, capture_output=True)
    result = subprocess.run(
        [str(python), "-I", str(probe), *(["--native"] if native else [])],
        cwd=scratch,
        check=True,
        text=True,
        capture_output=True,
    )
    reports.append(json.loads(result.stdout))
record = {
    "commit": manifest["commit"],
    "artifact": artifact.name,
    "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
    "cache_disabled": True,
    "base_and_native": reports,
    "status": "passed",
}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({"artifact": artifact.name, "status": "passed", "cache_disabled": True}))
