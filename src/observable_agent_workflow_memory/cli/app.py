"""Typer CLI for observable-agent-workflow-memory."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.table import Table

from observable_agent_workflow_memory.core.jsonio import loads_strict_json
from observable_agent_workflow_memory.core.models import ActionIntent
from observable_agent_workflow_memory.ports.plugins import list_entry_points
from observable_agent_workflow_memory.qualified.cli import app as qualified_app
from observable_agent_workflow_memory.runtime.kernel import AgentKernel

app = typer.Typer(help="Observable-only workflow memory for no-meta agents.")
plugins_app = typer.Typer(help="Inspect installed plugins.")
intent_app = typer.Typer(help="Create and inspect action intents.")
app.add_typer(plugins_app, name="plugins")
app.add_typer(intent_app, name="intent")
app.add_typer(qualified_app, name="qualified")
console = Console()


def _kernel(state: Path, model: str | None = None, profile: str = "strict") -> AgentKernel:
    return AgentKernel.open(state, model=model, profile=profile)


@app.command()
def init(
    path: Annotated[Path, typer.Argument(help="Project/state directory.")] = Path(".oawm"),
) -> None:
    """Initialize local state."""

    kernel = _kernel(path)
    del kernel
    console.print(f"Initialized OAWM state at [bold]{path}[/bold]")


@app.command()
def observe(
    file: Annotated[Path, typer.Argument(help="JSONL or JSON file to observe.")],
    run_id: Annotated[str | None, typer.Option(help="Run identifier.")] = None,
    kind: Annotated[str, typer.Option(help="Event kind for JSONL rows.")] = "observation",
    state: Annotated[Path, typer.Option(help="OAWM state directory.")] = Path(".oawm"),
) -> None:
    """Append observable events from a file."""

    kernel = _kernel(state)
    count = 0
    for payload in _read_payloads(file):
        event_kind = str(payload.pop("kind", kind)) if isinstance(payload, dict) else kind
        event_payload = payload if isinstance(payload, dict) else {"text": str(payload)}
        kernel.observe(event_kind, event_payload, run_id)
        count += 1
    console.print(f"Observed {count} event(s).")


@app.command()
def search(
    query: Annotated[str, typer.Argument(help="Search query.")],
    mode: Annotated[str, typer.Option(help="admissible, raw, candidate, or audit.")] = "admissible",
    limit: Annotated[int, typer.Option(help="Maximum result count.")] = 8,
    state: Annotated[Path, typer.Option(help="OAWM state directory.")] = Path(".oawm"),
) -> None:
    """Search memory records."""

    kernel = _kernel(state)
    results = kernel.retrieve(query, mode=mode, limit=limit)
    table = Table("lane", "memory_id", "score", "claim")
    for item in results:
        table.add_row(item.lane.value, item.memory_id, f"{item.score:.4f}", item.claim)
    console.print(table)


@app.command()
def propose(
    run_id: Annotated[str, typer.Option(help="Run identifier.")],
    scope: Annotated[str, typer.Option(help="Proposal scope.")] = "session",
    tool: Annotated[
        list[str] | None,
        typer.Option(help="Declared tool name; repeat for multiple tools."),
    ] = None,
    max_steps: Annotated[int | None, typer.Option(help="Declared max_steps cap.")] = None,
    interface_signature: Annotated[
        str,
        typer.Option(help="Workflow interface signature."),
    ] = "agent.workflow.v1",
    state: Annotated[Path, typer.Option(help="OAWM state directory.")] = Path(".oawm"),
) -> None:
    """Create a memory promotion candidate from observable events."""

    kernel = _kernel(state)
    resource_caps = {"max_steps": max_steps} if max_steps is not None else None
    candidate = kernel.propose_memory(
        run_id,
        scope=scope,
        tools=tool,
        resource_caps=resource_caps,
        interface_signature=interface_signature,
    )
    console.print(candidate.model_dump_json(indent=2))


@app.command()
def verify(
    candidate_id: Annotated[str, typer.Argument(help="Candidate memory id.")],
    action_intent: Annotated[
        Path | None,
        typer.Option(help="ActionIntent JSON file for action-bound verification."),
    ] = None,
    state: Annotated[Path, typer.Option(help="OAWM state directory.")] = Path(".oawm"),
) -> None:
    """Verify a memory promotion candidate."""

    kernel = _kernel(state)
    intent = _read_action_intent(action_intent) if action_intent is not None else None
    receipt = kernel.verify(candidate_id, action_intent=intent)
    console.print(receipt.model_dump_json(indent=2))
    if receipt.result != "passed":
        raise typer.Exit(code=2)


@app.command()
def promote(
    candidate_id: Annotated[str, typer.Argument(help="Candidate memory id.")],
    state: Annotated[Path, typer.Option(help="OAWM state directory.")] = Path(".oawm"),
) -> None:
    """Promote a verified candidate into certified workflow memory."""

    kernel = _kernel(state)
    record = kernel.promote(candidate_id)
    console.print(record.model_dump_json(indent=2))


@app.command()
def retire(
    memory_id: Annotated[str, typer.Argument(help="Memory id to tombstone.")],
    reason: Annotated[str, typer.Option(help="Observable reason for retirement.")],
    state: Annotated[Path, typer.Option(help="OAWM state directory.")] = Path(".oawm"),
) -> None:
    """Move a memory record to tombstone lane without deleting it."""

    kernel = _kernel(state)
    record = kernel.retire(memory_id, reason)
    console.print(record.model_dump_json(indent=2))


@app.command()
def contradict(
    memory_id: Annotated[str, typer.Argument(help="Memory id being contradicted.")],
    claim: Annotated[str, typer.Argument(help="Contradictory observable claim.")],
    reason: Annotated[str, typer.Option(help="Reason for recording contradiction.")],
    source_event_id: Annotated[
        list[str] | None,
        typer.Option(help="Observable event id supporting the contradiction."),
    ] = None,
    state: Annotated[Path, typer.Option(help="OAWM state directory.")] = Path(".oawm"),
) -> None:
    """Record a contradiction lane memory without erasing the original."""

    kernel = _kernel(state)
    record = kernel.contradict(memory_id, claim, source_event_id or [], reason)
    console.print(record.model_dump_json(indent=2))


@app.command()
def supersede(
    old_memory_id: Annotated[str, typer.Argument(help="Certified memory being superseded.")],
    new_memory_id: Annotated[str, typer.Argument(help="Certified replacement memory.")],
    receipt_id: Annotated[str, typer.Argument(help="Passing receipt for the new memory.")],
    state: Annotated[Path, typer.Option(help="OAWM state directory.")] = Path(".oawm"),
) -> None:
    """Move an old certified memory into superseded lane."""

    kernel = _kernel(state)
    record = kernel.supersede(old_memory_id, new_memory_id, receipt_id)
    console.print(record.model_dump_json(indent=2))


@app.command()
def correct(
    memory_id: Annotated[str, typer.Argument(help="Memory id to correct.")],
    corrected_claim: Annotated[str, typer.Argument(help="Replacement claim.")],
    source_event_id: Annotated[
        list[str] | None,
        typer.Option(help="Additional observable event id supporting the correction."),
    ] = None,
    run_id: Annotated[str | None, typer.Option(help="Run identifier.")] = None,
    state: Annotated[Path, typer.Option(help="OAWM state directory.")] = Path(".oawm"),
) -> None:
    """Create a correction candidate without directly promoting it."""

    kernel = _kernel(state)
    candidate = kernel.correct_memory(
        memory_id,
        corrected_claim,
        run_id=run_id,
        source_event_ids=source_event_id or [],
    )
    console.print(candidate.model_dump_json(indent=2))


@app.command()
def run(
    task: Annotated[str, typer.Argument(help="Task to run.")],
    model: Annotated[str | None, typer.Option(help="LiteLLM model id.")] = None,
    state: Annotated[Path, typer.Option(help="OAWM state directory.")] = Path(".oawm"),
    external_effects: Annotated[
        bool,
        typer.Option(help="Request external effects; strict mode blocks without gate receipts."),
    ] = False,
    gate_receipt_id: Annotated[
        list[str] | None,
        typer.Option(help="Action-bound passing receipt id allowed to open the ActionGate."),
    ] = None,
    action_intent: Annotated[
        Path | None,
        typer.Option(help="ActionIntent JSON file required for external effects."),
    ] = None,
) -> None:
    """Run a model-connected task with certified memory context."""

    kernel = _kernel(state, model=model)
    intent = _read_action_intent(action_intent) if action_intent is not None else None
    if external_effects and intent is None:
        console.print("[red]external effects require --action-intent[/red]")
        raise typer.Exit(code=2)
    result = kernel.run(
        task,
        external_effects=external_effects,
        model=model,
        gate_receipt_ids=gate_receipt_id,
        action_intent=intent,
    )
    console.print(result.content)


@app.command()
def audit(
    state: Annotated[Path, typer.Option(help="OAWM state directory.")] = Path(".oawm"),
    receipts: Annotated[bool, typer.Option(help="Verify and print receipt audit rows.")] = False,
    strict_recheck: Annotated[
        bool,
        typer.Option(help="Re-run checker set against current candidate and evidence."),
    ] = False,
) -> None:
    """Print audit counts."""

    kernel = _kernel(state)
    if receipts:
        table = Table(
            "receipt_id",
            "candidate_id",
            "result",
            "action",
            "integrity",
            "recheck",
            "verified",
            "reason",
        )
        for row in kernel.audit_receipts(strict_recheck=strict_recheck):
            table.add_row(
                str(row["receipt_id"]),
                str(row["candidate_id"]),
                str(row["result"]),
                str(row["bound_action_id"]),
                str(row["receipt_integrity"]),
                str(row["checker_recheck"]),
                str(row["verified"]),
                str(row["reason"]),
            )
        console.print(table)
        return
    table = Table("key", "count")
    for key, value in sorted(kernel.audit().items()):
        table.add_row(key, str(value))
    console.print(table)


@intent_app.command("create")
def intent_create(
    tool_name: Annotated[str, typer.Option(help="Tool or action name.")],
    effect_class: Annotated[str, typer.Option(help="Effect class, e.g. local-external.")],
    args_json: Annotated[str, typer.Option(help="Canonical action arguments as JSON object.")],
    max_steps: Annotated[int, typer.Option(help="Declared max_steps cap.")] = 32,
    required_contract_id: Annotated[
        str | None,
        typer.Option(help="Optional required workflow contract id."),
    ] = None,
    required_receipt_id: Annotated[
        str | None,
        typer.Option(help="Optional required receipt id."),
    ] = None,
) -> None:
    """Create an ActionIntent JSON document."""

    parsed = loads_strict_json(args_json)
    if not isinstance(parsed, dict):
        console.print("[red]--args-json must be a JSON object[/red]")
        raise typer.Exit(code=2)
    intent = ActionIntent.create(
        tool_name=tool_name,
        effect_class=effect_class,
        arguments=parsed,
        required_contract_id=required_contract_id,
        required_receipt_id=required_receipt_id,
        resource_caps={"max_steps": max_steps},
    )
    console.print(intent.to_json_text())


@plugins_app.command("list")
def plugins_list() -> None:
    """List installed entry-point plugins."""

    table = Table("group", "name", "value")
    for group, eps in list_entry_points().items():
        for ep in eps:
            table.add_row(group, ep.name, ep.value)
    console.print(table)


def _read_payloads(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    stripped = text.strip()
    if not stripped:
        return []
    if path.suffix.lower() == ".jsonl":
        return [
            _payload_item(loads_strict_json(line)) for line in stripped.splitlines() if line.strip()
        ]
    parsed = loads_strict_json(stripped)
    if isinstance(parsed, list):
        return [_payload_item(item) for item in parsed]
    if isinstance(parsed, dict):
        return [parsed]
    return [{"text": str(parsed)}]


def _payload_item(item: Any) -> dict[str, Any]:
    if isinstance(item, dict):
        return item
    return {"text": str(item)}


def _read_action_intent(path: Path) -> ActionIntent:
    return ActionIntent.from_json_text(path.read_text(encoding="utf-8"))


def main() -> None:
    app()


if __name__ == "__main__":
    main()
