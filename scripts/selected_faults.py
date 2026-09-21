"""Seven bounded implementation mutations, tested in disposable copies."""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
prefix = "src/observable_agent_workflow_memory/"
faults = [
    (
        "omitted-receiver",
        "qualified/eligibility.py",
        "if q.context != context or input_text not in context.inputs:",
        "if input_text not in context.inputs:",
        "tests/test_qualified.py::test_separate_context_mismatches",
    ),
    (
        "skipped-withdrawal",
        "qualified/eligibility.py",
        'if any(item["dependency"] in context.dependencies for item in state["withdrawn"]):',
        "if False:",
        "tests/test_qualified.py::test_independent_view_forgery_and_revocation",
    ),
    (
        "source-digest-bypass",
        "qualified/wire.py",
        "if sha(self.raw) != self.sha256:",
        "if False:",
        "tests/test_qualified.py::test_source_mutation_holdout_missing_mapping",
    ),
    (
        "exposure-as-success",
        "qualified/store.py",
        'state["exposures"].append(data)',
        'state["exposures"].append(data)\n            state["services"].append(entry.id)',
        "tests/test_qualified.py::test_boundaries_readonly_stale_and_explicit_exposure",
    ),
    (
        "duplicate-credit",
        "qualified/store.py",
        'if state["checked"][data["intent"]] and data["intent"] not in state["services"]:',
        'if state["checked"][data["intent"]]:',
        "tests/test_qualified_boundaries.py::test_duplicate_reconciliation_and_conflicting_use",
    ),
    (
        "hidden-unmapped",
        "qualified/native.py",
        "q.mapping != expected_mapping",
        "False",
        "tests/test_qualified.py::test_source_mutation_holdout_missing_mapping",
    ),
    (
        "waived-action-gate",
        "runtime/action_gate.py",
        "if not self.strict:",
        "if True:",
        "tests/test_qualified.py::test_action_gate_cannot_be_waived",
    ),
]
results = []
for name, path, before, after, test in faults:
    with tempfile.TemporaryDirectory(prefix="oawm-fault-") as directory:
        copy = Path(directory)
        for folder in ("src", "tests", "schemas", "migrations", "examples"):
            shutil.copytree(
                root / folder, copy / folder, ignore=shutil.ignore_patterns("__pycache__")
            )
        target = copy / (prefix + path)
        text = target.read_text()
        assert text.count(before) == 1, (name, "mutation anchor drift")
        target.write_text(text.replace(before, after))
        import os

        env = dict(os.environ, PYTHONPATH=str(copy / "src"))
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test, "-q", "--tb=short", "--no-cov"],
            cwd=copy,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
        )
        caught = result.returncode == 1 and (
            "AssertionError" in result.stdout or "DID NOT RAISE" in result.stdout
        )
        results.append({"fault": name, "detected_by_assertion": caught})
        if not caught:
            print(result.stdout[-5000:])
print(json.dumps({"selected_faults": results, "denominator": len(faults)}, indent=2))
assert all(item["detected_by_assertion"] for item in results)
