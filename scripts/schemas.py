"""Generate additive schemas without rewriting legacy schema 1.1 identities."""

import json
import sys
from pathlib import Path

from observable_agent_workflow_memory.qualified.wire import (
    Context,
    Cost,
    Entry,
    Operation,
    Qualification,
    Source,
)

root = Path(__file__).resolve().parents[1] / "schemas" / "qualified"
root.mkdir(exist_ok=True)
for model in (Context, Cost, Entry, Operation, Qualification, Source):
    value = model.model_json_schema()
    value["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    value["$id"] = "https://kadubon.github.io/oawm/qualified/v1/" + model.__name__ + ".schema.json"
    text = json.dumps(value, indent=2) + "\n"
    path = root / (model.__name__ + ".schema.json")
    if "--check" in sys.argv:
        assert path.read_text() == text, path
    else:
        path.write_text(text, encoding="utf-8", newline="\n")
