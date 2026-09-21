"""Explicit qualified namespace; inspection never initializes state."""

from __future__ import annotations

import json
from importlib.resources import files
from pathlib import Path
from typing import Any

import typer

from .native import ccr_proposal, reconstruct
from .store import Store
from .wire import Context, Qualification, loads

app = typer.Typer(help="Opt-in finite receiver reuse; reports are not execution permission.")


def output(value: Any) -> None:
    typer.echo(json.dumps(value, sort_keys=True))


@app.command()
def example() -> None:
    """Run synthetic local effects in a disposable directory; pinned ALT/CCR required."""
    from .example import run

    output(run())


@app.command()
def inspect(database: Path) -> None:
    """Read-only bounded lifecycle replay. Exit zero means a report, not eligibility."""
    output(Store(database).inspect())


@app.command()
def check(file: Path, now: int) -> None:
    """Reconstruct native source qualification; does not admit or execute it."""
    q = Qualification.model_validate(loads(file.read_text(encoding="utf-8")))
    reconstruct(q, now)
    output(
        {
            "structural_qualification": "checked",
            "local_admission": None,
            "execution_authority": None,
        }
    )


@app.command()
def export(file: Path) -> None:
    """Emit an inert native CCR task proposal and explicit partial sidecars."""
    q = Qualification.model_validate(loads(file.read_text(encoding="utf-8")))
    output(ccr_proposal(q))


@app.command()
def resources() -> None:
    """List installed bundled schemas/migrations without a checkout."""
    root = files("observable_agent_workflow_memory").joinpath("resources")
    output(
        {
            name: sorted(item.name for item in root.joinpath(name).iterdir())
            for name in ("schemas", "migrations")
        }
    )


@app.command()
def retrieve(database: Path, policy: Path, receiver: str, input_text: str, now: int) -> None:
    """Read-only retrieval using explicitly supplied host context configuration."""
    from .runtime import ReceiverRuntime

    profiles = [Context.model_validate(item) for item in loads(policy.read_text(encoding="utf-8"))]
    output(ReceiverRuntime(None, database, profiles).retrieve(receiver, input_text, now=now))
