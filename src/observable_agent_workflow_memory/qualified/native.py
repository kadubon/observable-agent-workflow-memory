"""Pinned optional runtimes; finite source mapping and separate reconstruction."""

from __future__ import annotations

import importlib
import inspect
import json
from importlib.metadata import PackageNotFoundError, version
from importlib.resources import files
from typing import Any

from observable_agent_workflow_memory.core.canonical import digest_json

from .wire import Context, Cost, Operation, Qualification, Source, digest, encoded, sha

SLOT_MAP = {
    "steps[0].primitive": "$.tool",
    "steps[0].arguments[0]": "$.input",
    "checked_artifact": "$.implementation",
    "dependencies[0]": "$.implementation",
    "input_digest": "$.input",
    "check_results[0]": "$.input,$.output,$.outcome,$.complete",
    "time": "$.time",
    "split": "$.split",
    "complete": "$.complete",
    "outcome": "$.outcome",
    "costs[0]": "$.cost.id",
    "source_version": "$.version",
    "original_receiver_evidence": "$.receiver,$.context_digest",
}


def normalize(text: str) -> str:
    if not isinstance(text, str) or len(text) > 4096:
        raise ValueError("bounded text required")
    return "\n".join(sorted(set(text.splitlines())))


def checked(operation: Operation) -> bool:
    """Independent output invariant, not a producer success flag."""
    lines = operation.output.split("\n") if operation.output else []
    expected = set(operation.input.splitlines())
    if operation.input and not operation.output:
        lines = [""]
    return (
        operation.implementation == IMPLEMENTATION
        and operation.complete
        and operation.outcome == "success"
        and len(lines) == len(set(lines))
        and set(lines) == expected
        and all(a < b for a, b in zip(lines, lines[1:], strict=False))
    )


IMPLEMENTATION = sha(inspect.getsource(normalize).replace("\r\n", "\n"))


def runtime(module: str, package: str = "alt-foundry-kernel", expected: str = "0.5.0") -> Any:
    try:
        observed = version(package)
    except PackageNotFoundError as exc:
        raise ValueError(
            f"optional_dependency_required: install pinned {package} {expected}; "
            "see alt-interoperability.md"
        ) from exc
    if observed != expected:
        raise ValueError("unsupported companion version")
    return importlib.import_module(module)


def resources() -> Any:
    return files(__package__).joinpath("resources")


def pinned(name: str) -> Any:
    manifest = json.loads(resources().joinpath("manifest.json").read_text())
    row = next((r for r in manifest if r["file"] == name), None)
    if row is None:
        raise ValueError("unknown pinned resource")
    import hashlib

    raw = resources().joinpath(name).read_bytes()
    if hashlib.sha256(raw).hexdigest() != row["sha256"]:
        raise ValueError("companion file hash mismatch")
    return json.loads(raw)


def operation(source: Source) -> Operation:
    raw = source.read()
    if digest_json(raw) != source.producer_digest:
        raise ValueError("producer digest mismatch")
    return Operation.model_validate(raw)


def form(
    training: list[Source], context: Context, cutoff: int, cost: Cost
) -> tuple[dict[str, Any], dict[str, Any], dict[str, str]]:
    if not 2 <= len(training) <= 8:
        raise ValueError("formation source count limit")
    formation = runtime("alt_foundry_kernel.reuse.formation")
    wire = runtime("alt_foundry_kernel.reuse.wire")
    traces = []
    mapping = {}
    for source in training:
        op = operation(source)
        if op.split != "training" or op.time > cutoff:
            raise ValueError("holdout or post-cutoff source")
        traces.append(
            wire.envelope(
                {
                    "version": "alt_reuse_trace_v1",
                    "episode": source.event_id,
                    "task": context.task_family,
                    "input_digest": wire.digest(op.input),
                    "source_version": op.version,
                    "time": op.time,
                    "split": "training",
                    "complete": op.complete,
                    "checked_artifact": IMPLEMENTATION,
                    "steps": [
                        {"primitive": op.tool, "arguments": [{"kind": "string", "value": op.input}]}
                    ],
                    "outcome": op.outcome,
                    "check_results": ["pass" if checked(op) else "fail"],
                    "costs": [op.cost.id],
                    "guards": ["bounded-text"],
                    "dependencies": [IMPLEMENTATION],
                    "unresolved": [],
                    "secret_taint": False,
                }
            ).model_dump()
        )
        mapping.update({source.event_id + ":" + slot: field for slot, field in SLOT_MAP.items()})
    request = formation.Formation.model_validate(
        {
            "version": "alt_reuse_formation_v1",
            "mode": "sequence",
            "scope": context.mission,
            "cutoff": cutoff,
            "sources": traces,
            "library": [
                {
                    "id": "normalize-lines-v1",
                    "implementation": IMPLEMENTATION,
                    "inputs": ["string"],
                    "output": "string",
                }
            ],
            "parameters": [{"name": "text", "step": 0, "argument": 0}],
            "attempt_id": "form-" + digest(training_as_json(training))[:20],
            "cost_id": cost.id,
            "cost_unit": cost.unit,
            "cost": cost.amount,
            "expansion_limit": 8,
        }
    )
    candidate = formation.form(request)
    formation.reconstruct(request, candidate)
    return request.model_dump(), candidate.model_dump(), mapping


def training_as_json(sources: list[Source]) -> list[dict[str, Any]]:
    return [source.model_dump() for source in sources]


def _propose(
    *,
    memory_id: str,
    update_id: str,
    workflow_digest: str,
    context: Context,
    training: list[Source],
    evaluation: list[Source],
    cutoff: int,
    valid_from: int,
    valid_until: int,
    formation_cost: Cost,
) -> Qualification:
    request, candidate, mapping = form(training, context, cutoff, formation_cost)
    wire = runtime("alt_foundry_kernel.reuse.wire")
    costs = [formation_cost, *[operation(s).cost for s in training + evaluation]]
    common = dict(
        candidate=wire.digest(candidate),
        receiver=context.receiver,
        mission=context.mission,
        context=context.context,
        task_family=context.task_family,
        protocol=context.protocol,
        evaluator=context.evaluator,
        restrictions=context.restrictions,
        dependencies=context.dependencies,
        preconditions=["bounded-text"],
        postconditions=["sorted-unique-lines"],
        quality="exact",
        estimand="normalized-text",
        valuation="synthetic-work-v1",
        evidence_basis="source-replay",
    )
    checks = []
    for source in evaluation:
        op = operation(source)
        checks.append(
            wire.envelope(
                dict(
                    common,
                    version="alt_reuse_check_v1",
                    input_digest=wire.digest(op.input),
                    time=op.time,
                    result="pass" if checked(op) else "fail",
                    defeaters=[],
                )
            ).model_dump()
        )
    offer = dict(
        common,
        version="alt_reuse_offer_v1",
        inputs=[wire.digest(v) for v in context.inputs],
        opportunities=["local-use"],
        valid_from=valid_from,
        valid_until=valid_until,
        checks=checks,
        required_cost_ids=sorted({c.id for c in costs}),
        comparator="scratch",
    )
    result = Qualification(
        memory_id=memory_id,
        update_id=update_id,
        workflow_digest=workflow_digest,
        context=context,
        valid_from=valid_from,
        valid_until=valid_until,
        cutoff=cutoff,
        training=training,
        evaluation=evaluation,
        formation=request,
        candidate=candidate,
        offer=offer,
        mapping=mapping,
        costs=costs,
    )
    reconstruct(result, max(operation(s).time for s in evaluation))
    return result


def reconstruct(q: Qualification, now: int) -> None:
    """Check source-slot mapping directly; never call form/propose here."""
    encoded(q)
    q = Qualification.model_validate(q.model_dump())
    f = runtime("alt_foundry_kernel.reuse.formation")
    w = runtime("alt_foundry_kernel.reuse.wire")
    n = runtime("alt_foundry_kernel.reuse.qualification")
    request, candidate, offer = (
        f.Formation.model_validate(q.formation),
        f.Candidate.model_validate(q.candidate),
        n.Offer.model_validate(q.offer),
    )
    if (
        q.context.tool_version != "normalize-lines-v1"
        or q.context.evaluator != "normalize-checker-v1"
        or q.context.protocol != "normalize-protocol-v1"
        or q.context.dependencies != [IMPLEMENTATION]
        or q.context.checks != ["normalize-checker-v1"]
        or q.context.restrictions != ["local-only"]
    ):
        raise ValueError("unsupported registered receiver policy")
    if (
        request.cutoff != q.cutoff
        or request.scope != q.context.mission
        or len(request.sources) != len(q.training)
    ):
        raise ValueError("projection scope mismatch")
    expected_mapping = {
        source.event_id + ":" + slot: field
        for source in q.training
        for slot, field in SLOT_MAP.items()
    }
    if (
        q.mapping != expected_mapping
        or request.library[0].implementation != IMPLEMENTATION
        or len(request.library) != 1
        or request.library[0].inputs != ["string"]
        or request.library[0].output != "string"
    ):
        raise ValueError("hidden unmapped field or implementation")
    for source, projected in zip(q.training, request.sources, strict=True):
        op = operation(source)
        t = f.Trace.model_validate(projected.read())
        if (
            op.split != "training"
            or op.time > q.cutoff
            or not checked(op)
            or t.episode != source.event_id
            or t.input_digest != w.digest(op.input)
            or t.steps[0].primitive != op.tool
            or len(t.steps) != 1
            or [a.model_dump() for a in t.steps[0].arguments]
            != [{"kind": "string", "value": op.input}]
            or t.checked_artifact != IMPLEMENTATION
            or t.dependencies != [IMPLEMENTATION]
            or t.time != op.time
            or t.source_version != op.version
            or t.split != "training"
            or t.outcome != op.outcome
            or t.complete != op.complete
            or t.check_results != ["pass"]
            or t.costs != [op.cost.id]
            or t.guards != ["bounded-text"]
            or t.unresolved
            or t.secret_taint
        ):
            raise ValueError("unsupported_projection: source slot mismatch or failed trace")
    if len({s.event_id for s in q.training + q.evaluation}) != len(q.training + q.evaluation):
        raise ValueError("training/evaluation identities overlap")
    if (offer.valid_from, offer.valid_until) != (q.valid_from, q.valid_until):
        raise ValueError("validity binding mismatch")
    if (
        offer.postconditions != ["sorted-unique-lines"]
        or offer.preconditions != ["bounded-text"]
        or offer.evidence_basis != "source-replay"
        or offer.quality != "exact"
        or offer.estimand != "normalized-text"
        or offer.valuation != "synthetic-work-v1"
    ):
        raise ValueError("unsupported semantic scope")
    for field in (
        "receiver",
        "mission",
        "context",
        "task_family",
        "protocol",
        "evaluator",
        "dependencies",
        "restrictions",
    ):
        if getattr(offer, field) != getattr(q.context, field):
            raise ValueError("receiver context mismatch: " + field)
    if offer.inputs != [w.digest(v) for v in q.context.inputs] or len(offer.checks) != len(
        q.evaluation
    ):
        raise ValueError("finite input evidence mismatch")
    for source, projected in zip(q.evaluation, offer.checks, strict=True):
        op, check = operation(source), n.Check.model_validate(projected.read())
        if (
            op.split != "evaluation"
            or op.receiver != q.context.receiver
            or op.context_digest != digest(q.context)
            or op.time <= q.cutoff
            or not checked(op)
            or check.input_digest != w.digest(op.input)
            or check.time != op.time
            or op.input not in q.context.inputs
        ):
            raise ValueError("receiver domain evidence mismatch")
    expected_costs = {operation(s).cost.id: operation(s).cost for s in q.training + q.evaluation}
    expected_costs[request.cost_id] = Cost(
        id=request.cost_id, stage="formation", unit=request.cost_unit, amount=request.cost
    )
    actual = {cost.id: cost for cost in q.costs}
    if (
        len(actual) != len(q.costs)
        or actual != expected_costs
        or set(offer.required_cost_ids) != set(actual)
    ):
        raise ValueError("cost obligations omitted or conflicting")
    from jsonschema import Draft202012Validator
    from referencing import Registry

    for name, value in (("formation", q.formation), ("candidate", q.candidate), ("offer", q.offer)):
        Draft202012Validator(pinned("alt-" + name + ".schema.json"), registry=Registry()).validate(
            value
        )
    f.reconstruct(request, candidate)
    n.qualify(request, candidate, offer, now)


def ccr_proposal(q: Qualification) -> dict[str, Any]:
    validator = runtime("ccr.schemas.validation", "collective-capability-runtime", "1.8.0")
    task = pinned("ccr-task.json")
    task["task_id"] = "oawm-" + digest(q)[:24]
    task["title"] = "Review receiver-qualified OAWM procedure"
    task["objective"] = "Revalidate the exact OAWM revision, receiver and source evidence."
    task["inputs"] = [
        {
            "kind": "file",
            "ref": "oawm-qualification.json",
            "required": True,
            "notes": "Digest-bound inert sidecar: " + digest(q),
        }
    ]
    task["pic_interop"]["enabled"] = False
    task["pic_interop"]["recommended_pic_commands"] = []
    task["expected_outputs"][0]["acceptance_criteria"] = [
        "Current OAWM revision and receiver evidence independently rechecked.",
        "Host admission remains required; no lease or execution is granted.",
    ]
    task["extensions"] = {"x_oawm_qualification_digest": digest(q)}
    result = validator.validate_instance("task", task)
    if not result.ok:
        raise ValueError(str(result.errors))
    return {
        "native_task": task,
        "host_admission_required": True,
        "sidecar": {
            "qualification": q.model_dump(),
            "completion": (
                "Recheck current local revision and exact receiver evidence; "
                "obtain host admission before any use."
            ),
            "unmapped_obligations": [
                "CCR does not enforce OAWM receiver sidecars",
                "current OAWM invalidation snapshot required",
            ],
        },
        "execution_authority": None,
        "vek": {
            "status": "partial",
            "missing": ["native capacity registration and source journal"],
        },
        "cait": {
            "status": "partial",
            "missing": ["registered source-accounting contract and origin evidence"],
        },
    }


class AttemptError(ValueError):
    """Failed read-only attempt retains explicit payable modeled obligations."""

    def __init__(self, reason: str, costs: list[Cost]):
        super().__init__(reason)
        self.payable_costs = [cost.model_dump() for cost in costs]
        self.unmapped_obligations = [
            "Source costs unavailable from malformed source remain unresolved."
        ]


def propose(
    *,
    memory_id: str,
    update_id: str,
    workflow_digest: str,
    context: Context,
    training: list[Source],
    evaluation: list[Source],
    cutoff: int,
    valid_from: int,
    valid_until: int,
    formation_cost: Cost,
) -> Qualification:
    costs = [formation_cost]
    try:
        costs.extend(operation(source).cost for source in training + evaluation)
        return _propose(
            memory_id=memory_id,
            update_id=update_id,
            workflow_digest=workflow_digest,
            context=context,
            training=training,
            evaluation=evaluation,
            cutoff=cutoff,
            valid_from=valid_from,
            valid_until=valid_until,
            formation_cost=formation_cost,
        )
    except ValueError as exc:
        raise AttemptError(str(exc), costs) from exc
