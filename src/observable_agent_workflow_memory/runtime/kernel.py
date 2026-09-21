"""High-level agent kernel."""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, cast

from observable_agent_workflow_memory.adapters.deterministic_proposer import (
    DeterministicWorkflowProposer,
)
from observable_agent_workflow_memory.adapters.fts_retriever import FTSRetriever
from observable_agent_workflow_memory.adapters.jsonschema_checker import create_default_checkers
from observable_agent_workflow_memory.adapters.litellm_provider import LiteLLMProvider
from observable_agent_workflow_memory.adapters.local_tools import LocalToolAdapter
from observable_agent_workflow_memory.adapters.mock_llm import MockLLMProvider
from observable_agent_workflow_memory.adapters.receipt_verifier import DefaultReceiptVerifier
from observable_agent_workflow_memory.adapters.sqlite_storage import SQLiteStorage
from observable_agent_workflow_memory.core.canonical import digest_json
from observable_agent_workflow_memory.core.errors import FailClosedError, NotFoundError
from observable_agent_workflow_memory.core.models import (
    ActionIntent,
    CheckerResult,
    Event,
    Lane,
    MemoryOperation,
    MemoryRecord,
    PromotionReceipt,
    RetrievedMemory,
    StoredEvent,
)
from observable_agent_workflow_memory.core.transitions import (
    admissible_lanes_for_mode,
    assert_transition_allowed,
)
from observable_agent_workflow_memory.ports.checker import Checker
from observable_agent_workflow_memory.ports.llm import LLMMessage, LLMProvider, LLMResult
from observable_agent_workflow_memory.ports.plugins import load_entry_point
from observable_agent_workflow_memory.ports.proposer import WorkflowProposer
from observable_agent_workflow_memory.ports.receipt import ReceiptVerifier
from observable_agent_workflow_memory.ports.retrieval import Retriever
from observable_agent_workflow_memory.ports.storage import StorageBackend
from observable_agent_workflow_memory.ports.tools import ToolAdapter, ToolCall, ToolResult
from observable_agent_workflow_memory.runtime.action_gate import ActionGate
from observable_agent_workflow_memory.runtime.promotion import MemoryPromotionPipeline


class AgentKernel:
    """Default orchestration facade."""

    def __init__(
        self,
        *,
        storage: StorageBackend,
        retriever: Retriever,
        llm_provider: LLMProvider,
        checkers: list[Checker],
        proposer: WorkflowProposer,
        tool_adapter: ToolAdapter,
        receipt_verifier: ReceiptVerifier,
        profile: str = "strict",
    ) -> None:
        self.storage = storage
        self.retriever = retriever
        self.llm_provider = llm_provider
        self.checkers = checkers
        self.proposer = proposer
        self.tool_adapter = tool_adapter
        self.receipt_verifier = receipt_verifier
        self.profile = profile
        self.promotion = MemoryPromotionPipeline(
            storage=storage,
            checkers=checkers,
            profile=profile,
        )
        self.action_gate = ActionGate(strict=profile == "strict")

    @classmethod
    def open(
        cls,
        path: str | Path,
        model: str | None = None,
        profile: str = "strict",
        plugins: dict[str, Any] | None = None,
    ) -> AgentKernel:
        plugin_map = plugins or {}
        state_path = Path(path)
        db_path = state_path if state_path.suffix == ".sqlite" else state_path / "oawm.sqlite"
        storage = plugin_map.get("storage")
        if storage is None:
            storage = SQLiteStorage(db_path)
        elif isinstance(storage, str):
            storage = _instantiate_plugin("oawm.storage_backends", storage, db_path)
        storage.initialize()

        retriever = plugin_map.get("retriever")
        if retriever is None:
            if not hasattr(storage, "search_memory"):
                msg = "custom storage does not expose search_memory; configure a retriever plugin"
                raise FailClosedError(msg)
            retriever = FTSRetriever(storage)
        elif isinstance(retriever, str):
            retriever = _instantiate_plugin("oawm.retrievers", retriever, storage)

        llm_provider = plugin_map.get("llm_provider")
        if llm_provider is None:
            llm_provider = LiteLLMProvider(model) if model else MockLLMProvider()
        elif isinstance(llm_provider, str):
            llm_provider = _instantiate_plugin("oawm.llm_providers", llm_provider, model)

        checkers = plugin_map.get("checkers")
        if checkers is None:
            checkers = create_default_checkers()
        elif isinstance(checkers, str):
            checkers = _instantiate_plugin("oawm.checkers", checkers)

        proposer = plugin_map.get("proposer")
        if proposer is None:
            proposer = DeterministicWorkflowProposer()
        elif isinstance(proposer, str):
            proposer = _instantiate_plugin("oawm.proposers", proposer)

        tool_adapter = plugin_map.get("tool_adapter")
        if tool_adapter is None:
            tool_adapter = LocalToolAdapter()
        elif isinstance(tool_adapter, str):
            tool_adapter = _instantiate_plugin("oawm.tool_adapters", tool_adapter)

        receipt_verifier = plugin_map.get("receipt_verifier")
        if receipt_verifier is None:
            receipt_verifier = DefaultReceiptVerifier()
        elif isinstance(receipt_verifier, str):
            receipt_verifier = _instantiate_plugin("oawm.receipt_verifiers", receipt_verifier)
        return cls(
            storage=storage,
            retriever=retriever,
            llm_provider=llm_provider,
            checkers=checkers,
            proposer=proposer,
            tool_adapter=tool_adapter,
            receipt_verifier=receipt_verifier,
            profile=profile,
        )

    def observe(
        self,
        kind: str,
        payload: dict[str, Any],
        run_id: str | None = None,
        parents: list[str] | None = None,
        index_as_raw: bool = True,
    ) -> StoredEvent:
        actual_run_id = run_id or f"run_{uuid.uuid4().hex[:12]}"
        stored = self._append_event(kind, payload, actual_run_id, parents=parents or [])
        if not index_as_raw:
            return stored
        claim = _payload_to_claim(kind, payload)
        raw = MemoryRecord.create(
            lane=Lane.RAW,
            claim=claim,
            source_event_ids=[stored.event_id],
            metadata={"kind": kind, "run_id": actual_run_id, "obs_seq": stored.obs_seq},
        )
        self.storage.upsert_memory_record(
            raw,
            operation=MemoryOperation.WRITE,
            event_id=stored.event_id,
        )
        return stored

    def _append_event(
        self,
        kind: str,
        payload: dict[str, Any],
        run_id: str,
        *,
        parents: list[str] | None = None,
    ) -> StoredEvent:
        event = Event.create(
            kind=kind,
            payload=payload,
            run_id=run_id,
            parents=parents or [],
        )
        return self.storage.append_event(event)

    def record_memory_operation(
        self,
        operation: MemoryOperation,
        *,
        run_id: str,
        memory_ids: list[str],
        details: dict[str, Any] | None = None,
    ) -> StoredEvent:
        memory_refs = [self._memory_ref(memory_id) for memory_id in memory_ids]
        return self.observe(
            f"memory_{operation.value}",
            {
                "operation": operation.value,
                "memory_ids": memory_ids,
                "memory_refs": memory_refs,
                "details": details or {},
            },
            run_id=run_id,
            index_as_raw=False,
        )

    def propose_memory(
        self,
        run_id: str,
        scope: str = "session",
        *,
        tools: list[str] | None = None,
        resource_caps: dict[str, int] | None = None,
        interface_signature: str | None = None,
    ) -> MemoryRecord:
        events = self.storage.list_events(run_id=run_id)
        if not events:
            raise FailClosedError(f"cannot propose memory without observable events: {run_id}")
        candidate = self.proposer.propose(events, scope=scope)
        metadata = dict(candidate.metadata)
        metadata.setdefault("proposal_scope", scope)
        metadata.setdefault("run_id", run_id)
        metadata["interface_signature"] = interface_signature or str(
            metadata.get("interface_signature", "agent.workflow.v1")
        )
        existing_tools = metadata.get("tools", [])
        if not isinstance(existing_tools, list):
            existing_tools = []
        metadata["tools"] = (
            list(tools) if tools is not None else [str(item) for item in existing_tools]
        )
        existing_caps = metadata.get("resource_caps")
        default_caps = {"max_steps": min(32, max(1, len(events) * 2))}
        if resource_caps is not None:
            metadata["resource_caps"] = dict(resource_caps)
        elif isinstance(existing_caps, dict):
            metadata["resource_caps"] = dict(existing_caps)
        else:
            metadata["resource_caps"] = default_caps
        candidate = MemoryRecord.create(
            lane=candidate.lane,
            claim=candidate.claim,
            source_event_ids=list(candidate.source_event_ids),
            metadata=metadata,
            evidence_refs=list(candidate.evidence_refs),
            supersedes=list(candidate.supersedes),
            contradicts=list(candidate.contradicts),
        )
        return self.storage.upsert_memory_record(
            candidate,
            operation=MemoryOperation.WRITE,
            reason=f"proposed from run {run_id}",
        )

    def verify(
        self,
        candidate_id: str,
        checker_set: str = "default",
        action_intent: ActionIntent | None = None,
    ) -> PromotionReceipt:
        del checker_set
        context = {"action_intent": action_intent} if action_intent is not None else None
        return self.promotion.verify(candidate_id, context=context)

    def promote(self, candidate_id: str) -> MemoryRecord:
        return self.promotion.promote(candidate_id)

    def correct_memory(
        self,
        memory_id: str,
        corrected_claim: str,
        *,
        run_id: str | None = None,
        source_event_ids: list[str] | None = None,
    ) -> MemoryRecord:
        original = self.storage.get_memory_record(memory_id)
        actual_run_id = run_id or str(original.metadata.get("run_id") or "correction")
        correction_event = self.record_memory_operation(
            MemoryOperation.CORRECT,
            run_id=actual_run_id,
            memory_ids=[memory_id],
            details={
                "corrected_claim": corrected_claim,
                "supporting_source_event_ids": source_event_ids or [],
            },
        )
        evidence_event_ids = [correction_event.event_id, *(source_event_ids or [])]
        candidate = MemoryRecord.create(
            lane=Lane.CANDIDATE,
            claim=corrected_claim,
            source_event_ids=evidence_event_ids,
            supersedes=[memory_id],
            metadata={
                "proposal_scope": "correction",
                "run_id": actual_run_id,
                "corrected_from": memory_id,
                "interface_signature": str(
                    original.metadata.get("interface_signature", "agent.workflow.v1")
                ),
                "resource_caps": {"max_steps": min(32, max(1, len(evidence_event_ids) * 2))},
                "steps": [
                    f"Correct memory {memory_id}",
                    "Verify supporting observable correction events",
                ],
            },
        )
        return self.storage.upsert_memory_record(
            candidate,
            operation=MemoryOperation.CORRECT,
            reason=f"correction candidate for {memory_id}",
            event_id=correction_event.event_id,
        )

    def retrieve(
        self,
        query: str,
        mode: str = "admissible",
        limit: int = 8,
        run_id: str | None = None,
    ) -> list[RetrievedMemory]:
        lanes = admissible_lanes_for_mode(mode)
        results = self.retriever.search(query, lane_filter=lanes, limit=limit)
        self.record_memory_operation(
            MemoryOperation.READ,
            run_id=run_id or "retrieval",
            memory_ids=[item.memory_id for item in results],
            details={"query": query, "mode": mode, "lane_filter": [lane.value for lane in lanes]},
        )
        return results

    def run(
        self,
        task: str,
        tools: list[dict[str, Any]] | None = None,
        external_effects: bool = False,
        model: str | None = None,
        run_id: str | None = None,
        gate_receipt_ids: list[str] | None = None,
        action_intent: ActionIntent | None = None,
    ) -> LLMResult:
        if external_effects and action_intent is not None:
            if action_intent.tool_name != "kernel.run":
                raise FailClosedError("kernel.run action intent must use tool_name='kernel.run'")
            if action_intent.args_digest != digest_json({"task": task}):
                raise FailClosedError("kernel.run task does not match action intent digest")
        gate_receipts = [
            self.storage.get_receipt(receipt_id) for receipt_id in (gate_receipt_ids or [])
        ]
        self.action_gate.ensure_allowed(
            external_effects=external_effects,
            receipts=gate_receipts,
            intent=action_intent,
            reason="kernel.run external_effects=True requires an explicit gate receipt",
        )
        actual_run_id = run_id or f"run_{uuid.uuid4().hex[:12]}"
        self.observe("task", {"task": task}, run_id=actual_run_id)
        memories = self.retrieve(task, mode="admissible", limit=5, run_id=actual_run_id)
        self.record_memory_operation(
            MemoryOperation.USE,
            run_id=actual_run_id,
            memory_ids=[item.memory_id for item in memories],
            details={"task": task, "mode": "admissible"},
        )
        memory_context = "\n".join(f"- {item.claim}" for item in memories)
        messages = [
            LLMMessage(
                role="system",
                content=(
                    "You are connected to observable workflow memory. "
                    "Use only certified memories provided in the context."
                ),
            ),
            LLMMessage(
                role="user",
                content=f"Certified memory:\n{memory_context}\n\nTask:\n{task}",
            ),
        ]
        result = self.llm_provider.complete(messages, tools=tools, model=model)
        self.observe(
            "llm_result",
            {"task": task, "content": result.content, "model": result.model},
            run_id=actual_run_id,
        )
        return result

    def invoke_tool(
        self,
        call: ToolCall,
        intent: ActionIntent,
        gate_receipt_ids: list[str] | None = None,
    ) -> ToolResult:
        if call.name != intent.tool_name:
            raise FailClosedError("tool call name does not match action intent")
        if digest_json(call.arguments) != intent.args_digest:
            raise FailClosedError("tool call arguments do not match action intent digest")
        if intent.required_contract_id is not None:
            contract = self.storage.get_contract(intent.required_contract_id)
            required_receipt = intent.required_receipt_id
            contract_receipt = contract.replay_spec.get("receipt_id")
            if required_receipt is not None and contract_receipt != required_receipt:
                raise FailClosedError("required contract is not bound to required receipt")
        gate_receipts = [
            self.storage.get_receipt(receipt_id) for receipt_id in (gate_receipt_ids or [])
        ]
        self.action_gate.ensure_allowed(
            external_effects=call.external_effect,
            receipts=gate_receipts,
            intent=intent,
        )
        context = {
            "action_gate_open": call.external_effect,
            "action_intent": intent.model_dump(mode="json"),
        }
        authorizer = getattr(self.tool_adapter, "authorized_context", None)
        if callable(authorizer):
            context = authorizer(context)
        return self.tool_adapter.invoke(call, context=context)

    def run_qualified(
        self,
        task: str,
        *,
        receiver_runtime: Any,
        receiver: str,
        input_text: str,
        now: int,
    ) -> LLMResult:
        """Opt-in qualified context exposure; never records procedural success."""
        if receiver_runtime.kernel is not self:
            raise FailClosedError("receiver runtime belongs to another kernel")
        return cast(LLMResult, receiver_runtime.run(task, receiver, input_text, now=now))

    def retire(self, memory_id: str, reason: str) -> MemoryRecord:
        record = self.storage.get_memory_record(memory_id)
        assert_transition_allowed(record.lane, Lane.TOMBSTONE)
        retired = record.moved(Lane.TOMBSTONE, reason=reason)
        stored = self.storage.upsert_memory_record(
            retired,
            operation=MemoryOperation.DELETE,
            reason=reason,
            receipt_id=retired.receipt_id,
        )
        self.record_memory_operation(
            MemoryOperation.DELETE,
            run_id=str(record.metadata.get("run_id") or "retire"),
            memory_ids=[memory_id],
            details={"reason": reason},
        )
        return stored

    def contradict(
        self,
        memory_id: str,
        claim: str,
        source_event_ids: list[str],
        reason: str,
    ) -> MemoryRecord:
        original = self.storage.get_memory_record(memory_id)
        event = self.record_memory_operation(
            MemoryOperation.CORRECT,
            run_id=str(original.metadata.get("run_id") or "contradiction"),
            memory_ids=[memory_id],
            details={"claim": claim, "reason": reason, "source_event_ids": source_event_ids},
        )
        contradiction = MemoryRecord.create(
            lane=Lane.CONTRADICTION,
            claim=claim,
            source_event_ids=[event.event_id, *source_event_ids],
            contradicts=[memory_id],
            metadata={
                "proposal_scope": "contradiction",
                "run_id": event.run_id,
                "reason": reason,
                "interface_signature": str(
                    original.metadata.get("interface_signature", "agent.workflow.v1")
                ),
                "tools": [],
                "resource_caps": {"max_steps": 4},
            },
        )
        return self.storage.upsert_memory_record(
            contradiction,
            operation=MemoryOperation.CORRECT,
            reason=reason,
            event_id=event.event_id,
        )

    def supersede(self, old_memory_id: str, new_memory_id: str, receipt_id: str) -> MemoryRecord:
        old = self.storage.get_memory_record(old_memory_id)
        new = self.storage.get_memory_record(new_memory_id)
        receipt = self.storage.get_receipt(receipt_id)
        if new.lane != Lane.CERTIFIED:
            raise FailClosedError("superseding memory must already be certified")
        if receipt.result != "passed" or receipt.candidate_id != new_memory_id:
            raise FailClosedError("supersede requires a passing receipt for the new memory")
        assert_transition_allowed(old.lane, Lane.SUPERSEDED)
        superseded = old.moved(
            Lane.SUPERSEDED,
            reason=f"superseded by {new_memory_id}",
            receipt_id=receipt_id,
        )
        stored = self.storage.upsert_memory_record(
            superseded,
            operation=MemoryOperation.REPLACE,
            reason=f"superseded by {new_memory_id}",
            receipt_id=receipt_id,
        )
        self.record_memory_operation(
            MemoryOperation.REPLACE,
            run_id=str(new.metadata.get("run_id") or "supersede"),
            memory_ids=[old_memory_id, new_memory_id],
            details={"receipt_id": receipt_id},
        )
        return stored

    def audit(self) -> dict[str, int]:
        return self.storage.audit_counts()

    def verify_receipt(self, receipt_id: str) -> CheckerResult:
        receipt = self.storage.get_receipt(receipt_id)
        manifest_id = next(
            (ref for ref in receipt.evidence_refs if ref.startswith("evm_")),
            "",
        )
        if not manifest_id:
            return CheckerResult(
                checker_name="receipt-reference",
                passed=False,
                reason="receipt has no evidence manifest reference",
            )
        try:
            candidate = self.storage.get_memory_record(receipt.candidate_id)
            manifest = self.storage.get_evidence_manifest(manifest_id)
        except NotFoundError as exc:
            return CheckerResult(
                checker_name="receipt-reference",
                passed=False,
                reason=str(exc),
            )
        return self.receipt_verifier.verify_receipt(
            receipt,
            manifest,
            {"candidate": candidate},
        )

    def audit_receipts(self, strict_recheck: bool = False) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for receipt in self.storage.list_receipts():
            integrity = self.verify_receipt(receipt.receipt_id)
            recheck = (
                self._strict_recheck_receipt(receipt)
                if strict_recheck and integrity.passed
                else None
            )
            rows.append(
                {
                    "receipt_id": receipt.receipt_id,
                    "candidate_id": receipt.candidate_id,
                    "candidate_update_id": receipt.candidate_update_id,
                    "result": receipt.result,
                    "bound_action_id": receipt.bound_action_id or "",
                    "verified": integrity.passed
                    if recheck is None
                    else integrity.passed and recheck.passed,
                    "receipt_integrity": integrity.passed,
                    "checker_recheck": recheck.passed if recheck is not None else None,
                    "reason": _join_reasons(integrity.reason, recheck.reason if recheck else ""),
                }
            )
        return rows

    def _strict_recheck_receipt(self, receipt: PromotionReceipt) -> CheckerResult:
        try:
            candidate = self.storage.get_memory_record(receipt.candidate_id)
            manifest_id = next(
                (ref for ref in receipt.evidence_refs if ref.startswith("evm_")),
                "",
            )
            if not manifest_id:
                return CheckerResult(
                    checker_name="strict-recheck",
                    passed=False,
                    reason="receipt has no evidence manifest reference",
                )
            manifest = self.storage.get_evidence_manifest(manifest_id)
        except NotFoundError as exc:
            return CheckerResult(checker_name="strict-recheck", passed=False, reason=str(exc))

        actual_event_digests: dict[str, str] = {}
        missing_source_event_ids: list[str] = []
        for event_id in candidate.source_event_ids:
            try:
                actual_event_digests[event_id] = self.storage.get_event(event_id).payload_digest
            except NotFoundError:
                missing_source_event_ids.append(event_id)

        context = {
            "actual_event_digests": actual_event_digests,
            "missing_source_event_ids": missing_source_event_ids,
        }
        evidence = manifest.model_dump(mode="json")
        checks = [
            checker.verify(candidate, evidence=evidence, context=context)
            for checker in self.checkers
        ]
        failed = [check for check in checks if not check.passed]
        return CheckerResult(
            checker_name="strict-recheck",
            passed=not failed,
            reason="; ".join(f"{check.checker_name}: {check.reason}" for check in failed),
            metrics={"failed_checkers": [check.checker_name for check in failed]},
        )

    def _memory_ref(self, memory_id: str) -> dict[str, str]:
        try:
            record = self.storage.get_memory_record(memory_id)
        except NotFoundError:
            return {"memory_id": memory_id, "update_id": "", "content_digest": ""}
        return {
            "memory_id": record.memory_id,
            "update_id": record.update_id,
            "content_digest": record.content_digest(),
        }


def _payload_to_claim(kind: str, payload: dict[str, Any]) -> str:
    if "text" in payload:
        return f"{kind}: {payload['text']}"
    if "task" in payload:
        return f"{kind}: {payload['task']}"
    if "content" in payload:
        return f"{kind}: {payload['content']}"
    return f"{kind}: {payload}"


def _events_to_candidate_claim(events: list[StoredEvent], scope: str) -> str:
    first = events[0]
    last = events[-1]
    kinds = ", ".join(sorted({event.kind for event in events}))
    return (
        f"Verified workflow candidate for {scope}: {len(events)} observable events "
        f"from obs_seq {first.obs_seq} to {last.obs_seq}; event kinds: {kinds}."
    )


def _instantiate_plugin(group: str, name: str, *args: Any) -> Any:
    factory = load_entry_point(group, name)
    if callable(factory):
        try:
            return factory(*args)
        except TypeError:
            if args and all(arg is None for arg in args):
                return factory()
            raise
    if args:
        msg = f"plugin {group}:{name} is not callable"
        raise FailClosedError(msg)
    return factory


def _join_reasons(*reasons: str) -> str:
    return "; ".join(reason for reason in reasons if reason)
