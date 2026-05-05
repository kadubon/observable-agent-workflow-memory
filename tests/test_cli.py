from __future__ import annotations

import json
import re

from typer.testing import CliRunner

from observable_agent_workflow_memory.cli.app import app

runner = CliRunner()


def test_cli_observe_propose_audit_smoke(tmp_path) -> None:  # type: ignore[no-untyped-def]
    state = tmp_path / ".oawm"
    events = tmp_path / "events.jsonl"
    events.write_text(json.dumps({"kind": "note", "text": "observable evidence"}) + "\n")

    result = runner.invoke(app, ["init", str(state)])
    assert result.exit_code == 0, result.output

    result = runner.invoke(app, ["observe", str(events), "--run-id", "demo", "--state", str(state)])
    assert result.exit_code == 0, result.output

    result = runner.invoke(app, ["propose", "--run-id", "demo", "--state", str(state)])
    assert result.exit_code == 0, result.output
    assert "mem_" in result.output
    candidate_id = re.search(r"mem_[0-9a-f]+", result.output)
    assert candidate_id is not None

    result = runner.invoke(app, ["verify", candidate_id.group(0), "--state", str(state)])
    assert result.exit_code == 0, result.output
    assert "passed" in result.output

    result = runner.invoke(app, ["promote", candidate_id.group(0), "--state", str(state)])
    assert result.exit_code == 0, result.output
    assert "certified" in result.output

    result = runner.invoke(
        app,
        [
            "correct",
            candidate_id.group(0),
            "corrected observable workflow",
            "--state",
            str(state),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "supersedes" in result.output

    result = runner.invoke(app, ["audit", "--state", str(state)])
    assert result.exit_code == 0, result.output
    assert "events" in result.output


def test_cli_action_bound_external_effect_flow(tmp_path) -> None:  # type: ignore[no-untyped-def]
    state = tmp_path / ".oawm"
    events = tmp_path / "events.jsonl"
    intent_path = tmp_path / "intent.json"
    task = "allowed external effect declaration"
    events.write_text(json.dumps({"kind": "note", "text": "gate evidence"}) + "\n")

    result = runner.invoke(
        app,
        ["observe", str(events), "--run-id", "gate", "--state", str(state)],
    )
    assert result.exit_code == 0, result.output
    result = runner.invoke(
        app,
        [
            "propose",
            "--run-id",
            "gate",
            "--tool",
            "kernel.run",
            "--max-steps",
            "2",
            "--state",
            str(state),
        ],
    )
    assert result.exit_code == 0, result.output
    candidate_id = re.search(r"mem_[0-9a-f]+", result.output)
    assert candidate_id is not None

    result = runner.invoke(
        app,
        [
            "intent",
            "create",
            "--tool-name",
            "kernel.run",
            "--effect-class",
            "external",
            "--args-json",
            json.dumps({"task": task}),
            "--max-steps",
            "2",
        ],
    )
    assert result.exit_code == 0, result.output
    intent_path.write_text(result.output, encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "verify",
            candidate_id.group(0),
            "--action-intent",
            str(intent_path),
            "--state",
            str(state),
        ],
    )
    assert result.exit_code == 0, result.output
    receipt_id = re.search(r"rcp_[0-9a-f]+", result.output)
    assert receipt_id is not None

    result = runner.invoke(
        app,
        [
            "run",
            task,
            "--external-effects",
            "--gate-receipt-id",
            receipt_id.group(0),
            "--state",
            str(state),
        ],
    )
    assert result.exit_code == 2

    result = runner.invoke(
        app,
        [
            "run",
            task,
            "--external-effects",
            "--gate-receipt-id",
            receipt_id.group(0),
            "--action-intent",
            str(intent_path),
            "--state",
            str(state),
        ],
    )
    assert result.exit_code == 0, result.output
    assert task in result.output

    result = runner.invoke(app, ["audit", "--receipts", "--state", str(state)])
    assert result.exit_code == 0, result.output
    assert "True" in result.output
