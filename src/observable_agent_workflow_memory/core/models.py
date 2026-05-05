"""Core domain models.

Every persisted object carries a schema version. The models are intentionally
provider-neutral and storage-neutral.
"""

from __future__ import annotations

import datetime as dt
import uuid
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from observable_agent_workflow_memory.core.canonical import digest_json

SCHEMA_VERSION = "1.1"


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.UTC).replace(microsecond=0)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class Lane(StrEnum):
    RAW = "raw"
    CANDIDATE = "candidate"
    SHADOW = "shadow"
    CERTIFIED = "certified"
    SUPERSEDED = "superseded"
    QUARANTINE = "quarantine"
    TOMBSTONE = "tombstone"
    CONTRADICTION = "contradiction"


class MemoryOperation(StrEnum):
    WRITE = "write"
    REPLACE = "replace"
    DELETE = "delete"
    READ = "read"
    USE = "use"
    VERIFY = "verify"
    CORRECT = "correct"
    PROMOTE = "promote"


class Event(StrictModel):
    schema_version: str = SCHEMA_VERSION
    event_id: str
    event_nonce: str = Field(default_factory=lambda: uuid.uuid4().hex)
    run_id: str
    agent_id: str = "default"
    kind: str
    payload: dict[str, Any]
    payload_digest: str
    parents: list[str] = Field(default_factory=list)
    created_at: dt.datetime = Field(default_factory=now_utc)

    @classmethod
    def create(
        cls,
        *,
        kind: str,
        payload: dict[str, Any],
        run_id: str,
        agent_id: str = "default",
        parents: list[str] | None = None,
    ) -> Event:
        parent_list = parents or []
        created_at = now_utc()
        event_nonce = uuid.uuid4().hex
        payload_digest = digest_json(payload)
        seed = {
            "schema_version": SCHEMA_VERSION,
            "event_nonce": event_nonce,
            "run_id": run_id,
            "agent_id": agent_id,
            "kind": kind,
            "payload_digest": payload_digest,
            "parents": parent_list,
            "created_at": created_at.isoformat(),
        }
        event_id = f"evt_{digest_json(seed)[:32]}"
        return cls(
            event_id=event_id,
            event_nonce=event_nonce,
            run_id=run_id,
            agent_id=agent_id,
            kind=kind,
            payload=payload,
            payload_digest=payload_digest,
            parents=parent_list,
            created_at=created_at,
        )


class StoredEvent(Event):
    obs_seq: int
    obs_time: dt.datetime
    collector_id: str = "local"
    collector_seq: int


class WorkflowContract(StrictModel):
    schema_version: str = SCHEMA_VERSION
    contract_id: str
    name: str
    description: str = ""
    interface_signature: str
    preconditions: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)
    postconditions: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    checkers: list[str] = Field(default_factory=list)
    replay_spec: dict[str, Any] = Field(default_factory=dict)
    resource_caps: dict[str, int] = Field(default_factory=lambda: {"max_steps": 32})
    version: str = "0.1.0"
    source_memory_id: str | None = None
    source_update_id: str | None = None
    created_at: dt.datetime = Field(default_factory=now_utc)

    @classmethod
    def from_candidate(cls, candidate: MemoryRecord, receipt: PromotionReceipt) -> WorkflowContract:
        steps = candidate.metadata.get("steps")
        if not isinstance(steps, list) or not steps:
            steps = [candidate.claim]
        receipt_id = receipt.receipt_id
        seed = {
            "candidate_id": candidate.memory_id,
            "candidate_update_id": candidate.update_id,
            "claim": candidate.claim,
            "source_event_ids": candidate.source_event_ids,
            "receipt_id": receipt_id,
            "receipt_digest": receipt.receipt_digest,
        }
        contract_id = f"wfc_{digest_json(seed)[:32]}"
        return cls(
            contract_id=contract_id,
            name=candidate.claim[:96] or "certified-workflow",
            description="Promoted from verified memory candidate.",
            interface_signature=str(candidate.metadata.get("interface_signature", "default")),
            preconditions=list(candidate.metadata.get("preconditions", [])),
            steps=[str(step) for step in steps],
            postconditions=list(candidate.metadata.get("postconditions", [])),
            tools=list(candidate.metadata.get("tools", [])),
            checkers=[check.checker_name for check in receipt.checks],
            replay_spec={
                "source_event_ids": candidate.source_event_ids,
                "candidate_update_id": candidate.update_id,
                "candidate_digest": candidate.content_digest(),
                "receipt_id": receipt_id,
                "receipt_digest": receipt.receipt_digest,
            },
            resource_caps=dict(candidate.metadata.get("resource_caps", {"max_steps": 32})),
            source_memory_id=candidate.memory_id,
            source_update_id=candidate.update_id,
        )


class MemoryRecord(StrictModel):
    schema_version: str = SCHEMA_VERSION
    memory_id: str
    update_id: str
    lane: Lane
    claim: str
    source_event_ids: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    supersedes: list[str] = Field(default_factory=list)
    contradicts: list[str] = Field(default_factory=list)
    workflow_contract_id: str | None = None
    receipt_id: str | None = None
    status_reason: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: dt.datetime = Field(default_factory=now_utc)
    updated_at: dt.datetime = Field(default_factory=now_utc)

    @field_validator("claim")
    @classmethod
    def claim_must_not_be_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            msg = "claim must not be empty"
            raise ValueError(msg)
        return value

    @classmethod
    def create(
        cls,
        *,
        lane: Lane,
        claim: str,
        source_event_ids: list[str],
        metadata: dict[str, Any] | None = None,
        evidence_refs: list[str] | None = None,
        supersedes: list[str] | None = None,
        contradicts: list[str] | None = None,
    ) -> MemoryRecord:
        content_seed = {
            "claim": claim,
            "source_event_ids": source_event_ids,
            "metadata": metadata or {},
            "supersedes": supersedes or [],
            "contradicts": contradicts or [],
        }
        seed = {"lane": lane.value, **content_seed}
        memory_id = f"mem_{digest_json(seed)[:32]}"
        update_id = cls.compute_update_id(memory_id, digest_json(content_seed))
        return cls(
            memory_id=memory_id,
            update_id=update_id,
            lane=lane,
            claim=claim,
            source_event_ids=source_event_ids,
            metadata=metadata or {},
            evidence_refs=evidence_refs or [],
            supersedes=supersedes or [],
            contradicts=contradicts or [],
        )

    @staticmethod
    def compute_update_id(memory_id: str, content_digest: str) -> str:
        return f"upd_{digest_json({'memory_id': memory_id, 'content_digest': content_digest})[:32]}"

    def content_digest(self) -> str:
        return digest_json(
            {
                "claim": self.claim,
                "source_event_ids": self.source_event_ids,
                "metadata": self.metadata,
                "supersedes": self.supersedes,
                "contradicts": self.contradicts,
            }
        )

    def moved(
        self,
        lane: Lane,
        *,
        reason: str = "",
        receipt_id: str | None = None,
    ) -> MemoryRecord:
        data = self.model_dump()
        data["lane"] = lane
        data["status_reason"] = reason
        data["receipt_id"] = receipt_id or self.receipt_id
        data["updated_at"] = now_utc()
        return MemoryRecord(**data)


class CheckerResult(StrictModel):
    schema_version: str = SCHEMA_VERSION
    checker_name: str
    passed: bool
    reason: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    metrics: dict[str, Any] = Field(default_factory=dict)


class EvidenceManifest(StrictModel):
    schema_version: str = SCHEMA_VERSION
    manifest_id: str
    candidate_id: str
    candidate_update_id: str
    input_event_ids: list[str]
    input_event_digests: dict[str, str] = Field(default_factory=dict)
    candidate_digest: str
    replay_digest: str
    declared_tools: list[str] = Field(default_factory=list)
    resource_caps: dict[str, int] = Field(default_factory=dict)
    created_at: dt.datetime = Field(default_factory=now_utc)

    @classmethod
    def create(
        cls,
        *,
        candidate: MemoryRecord,
        input_event_ids: list[str],
        input_event_digests: dict[str, str] | None = None,
        declared_tools: list[str] | None = None,
        resource_caps: dict[str, int] | None = None,
    ) -> EvidenceManifest:
        candidate_digest = candidate.content_digest()
        replay_digest = digest_json(
            {
                "candidate_id": candidate.memory_id,
                "candidate_update_id": candidate.update_id,
                "claim": candidate.claim,
                "input_event_ids": input_event_ids,
                "input_event_digests": input_event_digests or {},
                "candidate_digest": candidate_digest,
                "declared_tools": declared_tools or [],
                "resource_caps": resource_caps or {},
            }
        )
        seed = {
            "candidate_id": candidate.memory_id,
            "candidate_update_id": candidate.update_id,
            "input_event_ids": input_event_ids,
            "input_event_digests": input_event_digests or {},
            "candidate_digest": candidate_digest,
            "replay_digest": replay_digest,
        }
        return cls(
            manifest_id=f"evm_{digest_json(seed)[:32]}",
            candidate_id=candidate.memory_id,
            candidate_update_id=candidate.update_id,
            input_event_ids=input_event_ids,
            input_event_digests=input_event_digests or {},
            candidate_digest=candidate_digest,
            replay_digest=replay_digest,
            declared_tools=declared_tools or [],
            resource_caps=resource_caps or {},
        )


class ActionIntent(StrictModel):
    schema_version: str = SCHEMA_VERSION
    action_id: str
    tool_name: str
    effect_class: str
    args_digest: str
    required_contract_id: str | None = None
    required_receipt_id: str | None = None
    resource_caps: dict[str, int] = Field(default_factory=lambda: {"max_steps": 32})

    @classmethod
    def create(
        cls,
        *,
        tool_name: str,
        effect_class: str,
        arguments: dict[str, Any],
        required_contract_id: str | None = None,
        required_receipt_id: str | None = None,
        resource_caps: dict[str, int] | None = None,
    ) -> ActionIntent:
        caps = resource_caps or {"max_steps": 32}
        args_digest = digest_json(arguments)
        action_seed = {
            "tool_name": tool_name,
            "effect_class": effect_class,
            "args_digest": args_digest,
            "resource_caps": caps,
        }
        action_id = f"act_{digest_json(action_seed)[:32]}"
        return cls(
            action_id=action_id,
            tool_name=tool_name,
            effect_class=effect_class,
            args_digest=args_digest,
            required_contract_id=required_contract_id,
            required_receipt_id=required_receipt_id,
            resource_caps=caps,
        )

    @classmethod
    def from_json_text(cls, text: str) -> ActionIntent:
        from observable_agent_workflow_memory.core.jsonio import loads_strict_json

        payload = loads_strict_json(text)
        if not isinstance(payload, dict):
            msg = "ActionIntent JSON must be an object"
            raise ValueError(msg)
        return cls(**payload)

    def to_json_text(self) -> str:
        return self.model_dump_json(indent=2)


class PromotionReceipt(StrictModel):
    schema_version: str = SCHEMA_VERSION
    receipt_id: str
    verification_id: str
    receipt_digest: str
    candidate_id: str
    candidate_update_id: str
    bound_action_id: str | None = None
    profile: Literal["strict", "warn"] = "strict"
    checks: list[CheckerResult]
    result: Literal["passed", "failed"]
    evidence_refs: list[str] = Field(default_factory=list)
    created_at: dt.datetime = Field(default_factory=now_utc)

    @classmethod
    def create(
        cls,
        *,
        candidate: MemoryRecord,
        profile: Literal["strict", "warn"],
        checks: list[CheckerResult],
        evidence_refs: list[str] | None = None,
        bound_action_id: str | None = None,
    ) -> PromotionReceipt:
        result: Literal["passed", "failed"]
        result = "passed" if all(c.passed for c in checks) else "failed"
        receipt_digest = cls.compute_receipt_digest(
            candidate_id=candidate.memory_id,
            candidate_update_id=candidate.update_id,
            bound_action_id=bound_action_id,
            profile=profile,
            checks=checks,
            result=result,
            evidence_refs=evidence_refs or [],
        )
        verification_id = f"ver_{uuid.uuid4().hex}"
        receipt_seed = {"verification_id": verification_id, "receipt_digest": receipt_digest}
        return cls(
            receipt_id=f"rcp_{digest_json(receipt_seed)[:32]}",
            verification_id=verification_id,
            receipt_digest=receipt_digest,
            candidate_id=candidate.memory_id,
            candidate_update_id=candidate.update_id,
            bound_action_id=bound_action_id,
            profile=profile,
            checks=checks,
            result=result,
            evidence_refs=evidence_refs or [],
        )

    @staticmethod
    def compute_receipt_digest(
        *,
        candidate_id: str,
        candidate_update_id: str,
        bound_action_id: str | None,
        profile: Literal["strict", "warn"],
        checks: list[CheckerResult],
        result: Literal["passed", "failed"],
        evidence_refs: list[str],
    ) -> str:
        return digest_json(
            {
                "candidate_id": candidate_id,
                "candidate_update_id": candidate_update_id,
                "bound_action_id": bound_action_id,
                "profile": profile,
                "checks": [c.model_dump(mode="json") for c in checks],
                "result": result,
                "evidence_refs": evidence_refs,
            }
        )


class MemoryRevision(StrictModel):
    schema_version: str = SCHEMA_VERSION
    revision_id: str
    memory_id: str
    update_id: str
    content_digest: str
    operation: MemoryOperation
    before_lane: Lane | None = None
    after_lane: Lane
    reason: str = ""
    receipt_id: str | None = None
    event_id: str | None = None
    record: dict[str, Any] = Field(default_factory=dict)
    created_at: dt.datetime = Field(default_factory=now_utc)

    @classmethod
    def create(
        cls,
        *,
        record: MemoryRecord,
        operation: MemoryOperation,
        before_lane: Lane | None = None,
        reason: str = "",
        receipt_id: str | None = None,
        event_id: str | None = None,
    ) -> MemoryRevision:
        created_at = now_utc()
        content_digest = record.content_digest()
        seed = {
            "nonce": uuid.uuid4().hex,
            "memory_id": record.memory_id,
            "update_id": record.update_id,
            "content_digest": content_digest,
            "operation": operation.value,
            "before_lane": before_lane.value if before_lane else None,
            "after_lane": record.lane.value,
            "receipt_id": receipt_id,
            "event_id": event_id,
            "created_at": created_at.isoformat(),
        }
        return cls(
            revision_id=f"rev_{digest_json(seed)[:32]}",
            memory_id=record.memory_id,
            update_id=record.update_id,
            content_digest=content_digest,
            operation=operation,
            before_lane=before_lane,
            after_lane=record.lane,
            reason=reason,
            receipt_id=receipt_id,
            event_id=event_id,
            record=record.model_dump(mode="json"),
            created_at=created_at,
        )


class RetrievedMemory(StrictModel):
    memory_id: str
    update_id: str | None = None
    content_digest: str | None = None
    lane: Lane
    claim: str
    score: float = 0.0
    workflow_contract_id: str | None = None
    receipt_id: str | None = None
    source_event_ids: list[str] = Field(default_factory=list)
