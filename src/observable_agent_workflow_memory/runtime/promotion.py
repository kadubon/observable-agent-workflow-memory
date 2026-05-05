"""Memory promotion pipeline."""

from __future__ import annotations

from typing import Any

from observable_agent_workflow_memory.core.errors import FailClosedError, NotFoundError
from observable_agent_workflow_memory.core.models import (
    ActionIntent,
    CheckerResult,
    Event,
    EvidenceManifest,
    Lane,
    MemoryOperation,
    MemoryRecord,
    PromotionReceipt,
    WorkflowContract,
    now_utc,
)
from observable_agent_workflow_memory.core.transitions import assert_transition_allowed
from observable_agent_workflow_memory.ports.checker import Checker
from observable_agent_workflow_memory.ports.storage import StorageBackend


class MemoryPromotionPipeline:
    """Verifies candidates and promotes them into certified workflow records."""

    def __init__(
        self,
        *,
        storage: StorageBackend,
        checkers: list[Checker],
        profile: str = "strict",
    ) -> None:
        self.storage = storage
        self.checkers = checkers
        self.profile = profile

    def build_evidence(self, candidate: MemoryRecord) -> dict[str, Any]:
        input_event_digests, _missing = self._collect_event_digests(candidate)
        manifest = EvidenceManifest.create(
            candidate=candidate,
            input_event_ids=list(candidate.source_event_ids),
            input_event_digests=input_event_digests,
            declared_tools=list(candidate.metadata.get("tools", [])),
            resource_caps=dict(candidate.metadata.get("resource_caps", {})),
        )
        self.storage.create_evidence_manifest(manifest)
        return manifest.model_dump(mode="json")

    def verify(
        self,
        candidate_id: str,
        *,
        evidence: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> PromotionReceipt:
        candidate = self.storage.get_memory_record(candidate_id)
        actual_event_digests, missing_source_event_ids = self._collect_event_digests(candidate)
        checker_context = dict(context or {})
        checker_context["actual_event_digests"] = actual_event_digests
        checker_context["missing_source_event_ids"] = missing_source_event_ids
        supplied_evidence = evidence if evidence is not None else self.build_evidence(candidate)
        action_intent = _action_intent_from_context(checker_context)
        bound_action_id = action_intent.action_id if action_intent is not None else None
        checks: list[CheckerResult] = [
            checker.verify(candidate, evidence=supplied_evidence, context=checker_context)
            for checker in self.checkers
        ]
        evidence_refs = [
            str(supplied_evidence.get("manifest_id", "")),
            str(supplied_evidence.get("replay_digest", "")),
        ]
        if bound_action_id is not None:
            evidence_refs.append(bound_action_id)
        receipt = PromotionReceipt.create(
            candidate=candidate,
            profile="strict" if self.profile == "strict" else "warn",
            checks=checks,
            evidence_refs=evidence_refs,
            bound_action_id=bound_action_id,
        )
        self.storage.create_receipt(receipt)
        self._append_verify_event(candidate, receipt, supplied_evidence)
        if receipt.result != "passed":
            quarantined = candidate.moved(
                Lane.QUARANTINE,
                reason="; ".join(check.reason for check in checks if not check.passed),
                receipt_id=receipt.receipt_id,
            )
            self.storage.upsert_memory_record(
                quarantined,
                operation=MemoryOperation.VERIFY,
                reason="; ".join(check.reason for check in checks if not check.passed),
                receipt_id=receipt.receipt_id,
            )
        else:
            shadow = candidate.moved(
                Lane.SHADOW,
                reason="verified in shadow lane; promotion still requires explicit promote",
                receipt_id=receipt.receipt_id,
            )
            self.storage.upsert_memory_record(
                shadow,
                operation=MemoryOperation.VERIFY,
                reason="verified in shadow lane; promotion still requires explicit promote",
                receipt_id=receipt.receipt_id,
            )
        return receipt

    def promote(self, candidate_id: str) -> MemoryRecord:
        candidate = self.storage.get_memory_record(candidate_id)
        receipts = self.storage.list_receipts(candidate_id=candidate_id)
        passing = [
            receipt
            for receipt in receipts
            if receipt.result == "passed" and receipt.candidate_update_id == candidate.update_id
        ]
        if not passing:
            raise FailClosedError("promotion requires a passing receipt for this candidate update")
        receipt = passing[-1]
        assert_transition_allowed(candidate.lane, Lane.CERTIFIED)
        contract = WorkflowContract.from_candidate(candidate, receipt)
        self.storage.create_contract(contract)
        data = candidate.model_dump()
        data.update(
            {
                "lane": Lane.CERTIFIED,
                "workflow_contract_id": contract.contract_id,
                "receipt_id": receipt.receipt_id,
                "status_reason": "promoted with passing receipt",
                "updated_at": now_utc(),
            }
        )
        certified = MemoryRecord(**data)
        stored = self.storage.upsert_memory_record(
            certified,
            operation=MemoryOperation.PROMOTE,
            reason="promoted with passing receipt",
            receipt_id=receipt.receipt_id,
        )
        for superseded_id in candidate.supersedes:
            old = self.storage.get_memory_record(superseded_id)
            assert_transition_allowed(old.lane, Lane.SUPERSEDED)
            self.storage.upsert_memory_record(
                old.moved(
                    Lane.SUPERSEDED,
                    reason=f"superseded by {candidate.memory_id}",
                    receipt_id=receipt.receipt_id,
                ),
                operation=MemoryOperation.REPLACE,
                reason=f"superseded by {candidate.memory_id}",
                receipt_id=receipt.receipt_id,
            )
        self._append_promote_event(stored, receipt, contract)
        return stored

    def _collect_event_digests(self, candidate: MemoryRecord) -> tuple[dict[str, str], list[str]]:
        input_event_digests: dict[str, str] = {}
        missing: list[str] = []
        for event_id in candidate.source_event_ids:
            try:
                input_event_digests[event_id] = self.storage.get_event(event_id).payload_digest
            except NotFoundError:
                missing.append(event_id)
        return input_event_digests, missing

    def _append_verify_event(
        self,
        candidate: MemoryRecord,
        receipt: PromotionReceipt,
        evidence: dict[str, Any],
    ) -> None:
        run_id = str(candidate.metadata.get("run_id") or "verification")
        event = Event.create(
            kind=f"memory_{MemoryOperation.VERIFY.value}",
            payload={
                "operation": MemoryOperation.VERIFY.value,
                "memory_ids": [candidate.memory_id],
                "memory_refs": [_memory_ref(candidate)],
                "details": {
                    "receipt_id": receipt.receipt_id,
                    "verification_id": receipt.verification_id,
                    "receipt_digest": receipt.receipt_digest,
                    "result": receipt.result,
                    "checks": [
                        {
                            "checker_name": check.checker_name,
                            "passed": check.passed,
                            "reason": check.reason,
                        }
                        for check in receipt.checks
                    ],
                    "evidence_refs": [
                        str(evidence.get("manifest_id", "")),
                        str(evidence.get("replay_digest", "")),
                    ],
                },
            },
            run_id=run_id,
            parents=list(candidate.source_event_ids),
        )
        self.storage.append_event(event)

    def _append_promote_event(
        self,
        memory: MemoryRecord,
        receipt: PromotionReceipt,
        contract: WorkflowContract,
    ) -> None:
        run_id = str(memory.metadata.get("run_id") or "promotion")
        event = Event.create(
            kind=f"memory_{MemoryOperation.PROMOTE.value}",
            payload={
                "operation": MemoryOperation.PROMOTE.value,
                "memory_ids": [memory.memory_id],
                "memory_refs": [_memory_ref(memory)],
                "details": {
                    "receipt_id": receipt.receipt_id,
                    "verification_id": receipt.verification_id,
                    "receipt_digest": receipt.receipt_digest,
                    "workflow_contract_id": contract.contract_id,
                    "supersedes": memory.supersedes,
                },
            },
            run_id=run_id,
            parents=list(memory.source_event_ids),
        )
        self.storage.append_event(event)


def _memory_ref(memory: MemoryRecord) -> dict[str, str]:
    return {
        "memory_id": memory.memory_id,
        "update_id": memory.update_id,
        "content_digest": memory.content_digest(),
    }


def _action_intent_from_context(context: dict[str, Any]) -> ActionIntent | None:
    raw_intent = context.get("action_intent")
    if raw_intent is None:
        return None
    if isinstance(raw_intent, ActionIntent):
        return raw_intent
    if isinstance(raw_intent, dict):
        return ActionIntent(**raw_intent)
    msg = "action_intent context must be an ActionIntent or mapping"
    raise FailClosedError(msg)
