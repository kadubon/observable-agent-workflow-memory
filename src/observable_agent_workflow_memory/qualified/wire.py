"""Closed, bounded sidecars. Digests bind bytes, not source authentication."""

from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

LIMIT = 2_000_000
Id = Annotated[str, Field(pattern=r"^[A-Za-z0-9_.:-]{1,120}$")]
Hash = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Tick = Annotated[int, Field(ge=0, le=2**31)]


def loads(raw: str) -> Any:
    if len(raw.encode()) > LIMIT:
        raise ValueError("byte limit")

    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def reject(value: str) -> Any:
        raise ValueError("noninteger JSON number: " + value)

    try:
        value = json.loads(raw, object_pairs_hook=pairs, parse_float=reject, parse_constant=reject)
    except RecursionError as exc:
        raise ValueError("nesting limit") from exc
    pending = [(value, 0)]
    visits = 0
    while pending:
        item, depth = pending.pop()
        visits += 1
        if depth > 24 or visits > 50000:
            raise ValueError("traversal limit")
        if isinstance(item, dict):
            pending.extend((v, depth + 1) for v in item.values())
        elif isinstance(item, list):
            pending.extend((v, depth + 1) for v in item)
    return value


def encoded(value: Any) -> str:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    loads(raw)
    return raw


def sha(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def digest(value: Any) -> str:
    return sha(encoded(value))


class Closed(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, validate_assignment=True)


class Cost(Closed):
    id: Id
    stage: Literal["formation", "verification", "transfer", "refresh", "maintenance", "use"]
    unit: Literal["work-unit"] = "work-unit"
    amount: str

    @field_validator("amount")
    @classmethod
    def exact(cls, value: str) -> str:
        if len(value) > 81:
            raise ValueError("quantity limit")
        number = Fraction(value)
        if (
            number < 0
            or str(number) != value
            or max(number.numerator.bit_length(), number.denominator.bit_length()) > 128
        ):
            raise ValueError("noncanonical nonnegative rational required")
        return value


class Context(Closed):
    version: Literal["oawm_receiver_v1"] = "oawm_receiver_v1"
    workspace: Id
    receiver: Id
    mission: Id
    task_family: Id
    context: Id
    inputs: Annotated[list[str], Field(min_length=1, max_length=8)]
    protocol: Id = "normalize-protocol-v1"
    evaluator: Id = "normalize-checker-v1"
    tool_version: Id = "normalize-lines-v1"
    clock: Id
    dependencies: Annotated[list[Hash], Field(min_length=1, max_length=8)]
    checks: Annotated[list[Id], Field(min_length=1, max_length=8)]
    restrictions: Annotated[list[Id], Field(max_length=8)] = Field(
        default_factory=lambda: ["local-only"]
    )
    expose: bool = False

    @field_validator("inputs", "dependencies", "checks", "restrictions")
    @classmethod
    def distinct(cls, values: list[str]) -> list[str]:
        if len(values) != len(set(values)) or any(len(v) > 4096 for v in values):
            raise ValueError("duplicate or oversized domain")
        return values


class Source(Closed):
    event_id: Id
    producer_digest: Hash
    raw: str
    sha256: Hash

    def read(self) -> dict[str, Any]:
        if sha(self.raw) != self.sha256:
            raise ValueError("source digest mismatch")
        value = loads(self.raw)
        if not isinstance(value, dict):
            raise ValueError("source object required")
        return value


class Operation(Closed):
    version: Literal["oawm_normalize_v1"] = "oawm_normalize_v1"
    tool: Literal["normalize-lines-v1"] = "normalize-lines-v1"
    implementation: Hash
    input: Annotated[str, Field(max_length=4096)]
    output: Annotated[str, Field(max_length=4096)]
    receiver: Id
    context_digest: Hash
    time: Tick
    split: Literal["training", "evaluation"]
    complete: bool = True
    outcome: Literal["success", "failure", "unknown"]
    cost: Cost


class Qualification(Closed):
    version: Literal["oawm_qualification_v1"] = "oawm_qualification_v1"
    memory_id: Id
    update_id: Id
    workflow_digest: Hash
    context: Context
    valid_from: Tick
    valid_until: Tick
    cutoff: Tick
    training: Annotated[list[Source], Field(min_length=2, max_length=8)]
    evaluation: Annotated[list[Source], Field(min_length=1, max_length=8)]
    formation: dict[str, Any]
    candidate: dict[str, Any]
    offer: dict[str, Any]
    mapping: dict[str, str]
    costs: Annotated[list[Cost], Field(min_length=1, max_length=32)]
    source_authentication: None = None
    execution_authority: None = None


class Entry(Closed):
    version: Literal["oawm_lifecycle_v1"] = "oawm_lifecycle_v1"
    id: Id
    previous: Hash
    time: Tick
    kind: Literal[
        "admit",
        "exposure",
        "intent",
        "attempt",
        "outcome",
        "checked",
        "reconciled",
        "invalidate",
        "allegation",
        "withdraw",
        "cost",
        "correction",
    ]
    data: dict[str, Any]
