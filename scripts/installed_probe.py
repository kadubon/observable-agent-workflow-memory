"""Run only against installed files from an isolated interpreter outside checkout."""

import contextlib
import importlib.util
import io
import json
import runpy
import socket
import sys
from importlib.metadata import distribution, version
from importlib.resources import files
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from observable_agent_workflow_memory.cli.app import app


def forbidden(*args, **kwargs):
    raise AssertionError("runtime network forbidden")


native = "--native" in sys.argv
root = files("observable_agent_workflow_memory")
assert str(Path(sys.prefix).resolve()) in str(Path(str(root)).resolve())
assert importlib.util.find_spec("litellm") is None
assert version("observable-agent-workflow-memory") == "0.2.0b0"
with (
    patch.object(socket.socket, "connect", forbidden),
    patch.object(socket, "create_connection", forbidden),
):
    assert CliRunner().invoke(app, ["--help"]).exit_code == 0
    entry = next(
        e for e in distribution("observable-agent-workflow-memory").entry_points if e.name == "oawm"
    )
    assert callable(entry.load())
    resources = root.joinpath("resources")
    assert resources.joinpath("schemas", "qualified", "Qualification.schema.json").is_file()
    assert resources.joinpath("migrations", "003_receiver_events.sql").is_file()
    for name in (
        "certified_workflow_memory.py",
        "action_gate_external_effect.py",
        "semantic_checker_plugin.py",
    ):
        with contextlib.redirect_stdout(io.StringIO()):
            runpy.run_path(str(resources.joinpath("examples", name)), run_name="__main__")
    if native:
        from observable_agent_workflow_memory.qualified.example import run

        result = run()
        assert result["unique_services"] == 1
        assert result["costed_ALT_selected"] == ["scratch"]
    else:
        assert importlib.util.find_spec("alt_foundry_kernel") is None
        from observable_agent_workflow_memory.qualified.native import runtime

        try:
            runtime("alt_foundry_kernel.reuse.formation")
        except ValueError as exc:
            assert "optional_dependency_required" in str(exc)
        else:
            raise AssertionError("missing integration silently accepted")
        result = {"base_without_optional_packages": True}
print(
    json.dumps(
        {
            "package_version": version("observable-agent-workflow-memory"),
            "python": sys.version.split()[0],
            "origin": str(root),
            "environment": sys.prefix,
            "runtime_sockets": "blocked",
            "legacy_examples": 3,
            "new_profile": result,
        }
    )
)
