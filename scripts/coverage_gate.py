"""Separate statement/branch gates for all new profile modules, including unimported files."""

import json
import sys
from pathlib import Path

data = json.loads(Path(sys.argv[1]).read_text())
selected = {
    name: row for name, row in data["files"].items() if "/qualified/" in name.replace("\\", "/")
}
expected = {p.name for p in Path("src/observable_agent_workflow_memory/qualified").glob("*.py")}
assert {Path(name.replace("\\", "/")).name for name in selected} == expected
totals = {
    key: sum(row["summary"][key] for row in selected.values())
    for key in ("num_statements", "covered_lines", "num_branches", "covered_branches")
}
totals["statement_percent"] = 100 * totals["covered_lines"] / totals["num_statements"]
totals["branch_percent"] = 100 * totals["covered_branches"] / totals["num_branches"]
print(json.dumps({"new_profile": totals, "full_suite": data["totals"]}, indent=2))
assert totals["statement_percent"] >= 95
assert totals["branch_percent"] >= 90
