"""Bounded publication hygiene scan of versioned and intended source files."""

import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
paths = subprocess.check_output(
    ["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=root, text=True
).splitlines()
findings = []
for name in paths:
    path = root / name
    if path.suffix in {".sqlite", ".db", ".pem", ".p12"} or path.name == ".env":
        findings.append(name)
    if path.is_file() and path.suffix in {".py", ".md", ".json", ".toml", ".yml", ".txt"}:
        content = path.read_text(encoding="utf-8")
        if re.search(
            (
                r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|"
                r"[A-Z]:[\\/]Users[\\/]|gh[pousr]_[A-Za-z0-9]{30,}"
            ),
            content,
        ):
            findings.append(name)
assert not findings, findings
print("Publication scan passed; no configured private-path/key/state patterns found.")
