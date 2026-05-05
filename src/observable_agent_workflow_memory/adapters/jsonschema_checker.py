"""Default fail-closed promotion checkers."""

from __future__ import annotations

import math
from typing import Any

from jsonschema import Draft202012Validator
from pydantic import ValidationError

from observable_agent_workflow_memory.core.canonical import digest_json
from observable_agent_workflow_memory.core.models import (
    ActionIntent,
    CheckerResult,
    EvidenceManifest,
    Lane,
    MemoryRecord,
)
from observable_agent_workflow_memory.ports.checker import Checker

CANDIDATE_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["schema_version", "memory_id", "update_id", "lane", "claim", "source_event_ids"],
    "properties": {
        "schema_version": {"type": "string"},
        "memory_id": {"type": "string", "pattern": "^mem_"},
        "update_id": {"type": "string", "pattern": "^upd_"},
        "lane": {"enum": ["candidate", "shadow"]},
        "claim": {"type": "string", "minLength": 1},
        "source_event_ids": {
            "type": "array",
            "items": {"type": "string", "pattern": "^evt_"},
            "minItems": 1,
        },
    },
}


class CandidateSchemaChecker:
    checker_name = "candidate-schema"

    def __init__(self) -> None:
        self.validator = Draft202012Validator(CANDIDATE_SCHEMA)

    def verify(
        self,
        candidate: MemoryRecord,
        *,
        evidence: dict[str, Any],
        context: dict[str, Any],
    ) -> CheckerResult:
        del evidence, context
        payload = candidate.model_dump(mode="json")
        errors = sorted(self.validator.iter_errors(payload), key=lambda e: e.path)
        if errors:
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="; ".join(error.message for error in errors),
            )
        if candidate.lane not in {Lane.CANDIDATE, Lane.SHADOW}:
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason=f"candidate lane required, got {candidate.lane.value}",
            )
        return CheckerResult(checker_name=self.checker_name, passed=True)


class InputSetChecker:
    checker_name = "input-set"

    def verify(
        self,
        candidate: MemoryRecord,
        *,
        evidence: dict[str, Any],
        context: dict[str, Any],
    ) -> CheckerResult:
        expected_event_ids = list(candidate.source_event_ids)
        if len(expected_event_ids) != len(set(expected_event_ids)):
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="candidate source_event_ids must be unique",
            )

        input_event_ids = evidence.get("input_event_ids")
        if not isinstance(input_event_ids, list):
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="missing input_event_ids evidence",
            )
        observed_event_ids = [str(item) for item in input_event_ids]
        if observed_event_ids != expected_event_ids:
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="InputSet event ids must exactly match candidate source_event_ids",
            )

        missing_source_events = context.get("missing_source_event_ids", [])
        if missing_source_events:
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason=f"source events are not available in storage: {missing_source_events}",
            )

        input_event_digests = evidence.get("input_event_digests")
        if not isinstance(input_event_digests, dict):
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="missing input_event_digests evidence",
            )
        if any(
            not isinstance(event_id, str) or not isinstance(digest, str)
            for event_id, digest in input_event_digests.items()
        ):
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="input_event_digests must map event ids to digest strings",
            )
        if set(input_event_digests) != set(expected_event_ids):
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="InputSet digest ids must exactly match candidate source_event_ids",
            )

        actual_event_digests = context.get("actual_event_digests")
        if not isinstance(actual_event_digests, dict):
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="missing authoritative event digest context",
            )
        if any(
            not isinstance(event_id, str) or not isinstance(digest, str)
            for event_id, digest in actual_event_digests.items()
        ):
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="authoritative event digests must map event ids to digest strings",
            )
        if set(actual_event_digests) != set(expected_event_ids):
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="authoritative digest ids must exactly match candidate source_event_ids",
            )

        mismatched = [
            event_id
            for event_id in expected_event_ids
            if input_event_digests[event_id] != actual_event_digests[event_id]
        ]
        if mismatched:
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason=f"InputSet digest mismatch for source events: {mismatched}",
            )
        return CheckerResult(checker_name=self.checker_name, passed=True)


class CandidateDigestChecker:
    checker_name = "digest"

    def verify(
        self,
        candidate: MemoryRecord,
        *,
        evidence: dict[str, Any],
        context: dict[str, Any],
    ) -> CheckerResult:
        del context
        observed = evidence.get("candidate_digest")
        expected = candidate.content_digest()
        if observed != expected:
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="candidate_digest mismatch or missing",
                metrics={"expected": expected, "observed": observed},
            )
        expected_update_id = MemoryRecord.compute_update_id(candidate.memory_id, expected)
        if candidate.update_id != expected_update_id:
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="candidate update_id mismatch",
                metrics={"expected": expected_update_id, "observed": candidate.update_id},
            )
        return CheckerResult(checker_name=self.checker_name, passed=True)


class EvidenceManifestChecker:
    checker_name = "evidence-manifest"

    def verify(
        self,
        candidate: MemoryRecord,
        *,
        evidence: dict[str, Any],
        context: dict[str, Any],
    ) -> CheckerResult:
        del context
        try:
            manifest = EvidenceManifest(**evidence)
        except ValidationError as exc:
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason=f"invalid evidence manifest: {exc.errors()[0]['msg']}",
            )

        if manifest.candidate_id != candidate.memory_id:
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="evidence manifest candidate_id does not match candidate",
            )
        if manifest.candidate_update_id != candidate.update_id:
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="evidence manifest candidate_update_id does not match candidate",
            )

        expected_candidate_digest = candidate.content_digest()
        if manifest.candidate_digest != expected_candidate_digest:
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="evidence manifest candidate_digest mismatch",
                metrics={
                    "expected": expected_candidate_digest,
                    "observed": manifest.candidate_digest,
                },
            )

        expected_replay_digest = digest_json(
            {
                "candidate_id": candidate.memory_id,
                "candidate_update_id": candidate.update_id,
                "claim": candidate.claim,
                "input_event_ids": manifest.input_event_ids,
                "input_event_digests": manifest.input_event_digests,
                "candidate_digest": expected_candidate_digest,
                "declared_tools": manifest.declared_tools,
                "resource_caps": manifest.resource_caps,
            }
        )
        if manifest.replay_digest != expected_replay_digest:
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="evidence manifest replay_digest mismatch",
                metrics={
                    "expected": expected_replay_digest,
                    "observed": manifest.replay_digest,
                },
            )

        expected_manifest_id = (
            "evm_"
            + digest_json(
                {
                    "candidate_id": candidate.memory_id,
                    "candidate_update_id": candidate.update_id,
                    "input_event_ids": manifest.input_event_ids,
                    "input_event_digests": manifest.input_event_digests,
                    "candidate_digest": expected_candidate_digest,
                    "replay_digest": expected_replay_digest,
                }
            )[:32]
        )
        if manifest.manifest_id != expected_manifest_id:
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="evidence manifest_id mismatch",
                metrics={
                    "expected": expected_manifest_id,
                    "observed": manifest.manifest_id,
                },
            )

        return CheckerResult(checker_name=self.checker_name, passed=True)


class ResourceCapChecker:
    checker_name = "resource-caps"

    def __init__(self, max_steps: int = 128) -> None:
        self.max_steps = max_steps

    def verify(
        self,
        candidate: MemoryRecord,
        *,
        evidence: dict[str, Any],
        context: dict[str, Any],
    ) -> CheckerResult:
        resource_caps = candidate.metadata.get("resource_caps", {})
        evidence_caps = evidence.get("resource_caps", {})
        if not isinstance(resource_caps, dict):
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="candidate metadata resource_caps must be an object",
            )
        if evidence_caps != resource_caps:
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="evidence resource_caps must match candidate metadata",
            )
        action_intent = _action_intent_from_context(context)
        if action_intent is not None and action_intent.resource_caps != resource_caps:
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="action intent resource_caps must match candidate metadata",
            )
        contract_caps = context.get("workflow_contract_resource_caps")
        if contract_caps is not None and contract_caps != resource_caps:
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="workflow contract resource_caps must match candidate metadata",
            )
        tool_caps = context.get("tool_resource_caps")
        if tool_caps is not None and tool_caps != resource_caps:
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="tool runtime resource_caps must match candidate metadata",
            )
        max_steps = resource_caps.get("max_steps", 32) if isinstance(resource_caps, dict) else 32
        if not isinstance(max_steps, int) or max_steps < 1 or max_steps > self.max_steps:
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason=f"max_steps must be between 1 and {self.max_steps}",
            )
        return CheckerResult(checker_name=self.checker_name, passed=True)


class DeclaredToolsChecker:
    checker_name = "declared-tools"

    def verify(
        self,
        candidate: MemoryRecord,
        *,
        evidence: dict[str, Any],
        context: dict[str, Any],
    ) -> CheckerResult:
        metadata_tools = candidate.metadata.get("tools", [])
        if not isinstance(metadata_tools, list) or not all(
            isinstance(item, str) for item in metadata_tools
        ):
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="candidate metadata tools must be a list of strings",
            )
        declared_tools = evidence.get("declared_tools")
        if declared_tools != metadata_tools:
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="evidence declared_tools must match candidate metadata tools",
            )
        action_intent = _action_intent_from_context(context)
        if action_intent is not None and action_intent.tool_name not in metadata_tools:
            reason = "action intent tool is not declared by candidate: "
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason=f"{reason}{action_intent.tool_name}",
            )
        contract_tools = context.get("workflow_contract_tools")
        if contract_tools is not None and contract_tools != metadata_tools:
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="workflow contract tools must match candidate metadata tools",
            )
        tool_invocations = context.get("tool_invocations", [])
        if not isinstance(tool_invocations, list):
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="tool_invocations context must be a list",
            )
        undeclared = [
            str(item.get("tool_name"))
            for item in tool_invocations
            if isinstance(item, dict) and item.get("tool_name") not in metadata_tools
        ]
        if undeclared:
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason=f"tool invocations are not declared by candidate: {undeclared}",
            )
        return CheckerResult(checker_name=self.checker_name, passed=True)


class DeterministicBoundaryChecker:
    checker_name = "deterministic-boundary"

    def verify(
        self,
        candidate: MemoryRecord,
        *,
        evidence: dict[str, Any],
        context: dict[str, Any],
    ) -> CheckerResult:
        del context
        float_paths = [
            *_find_float_paths(candidate.metadata, "candidate.metadata"),
            *_find_float_paths(evidence, "evidence"),
        ]
        if float_paths:
            return CheckerResult(
                checker_name=self.checker_name,
                passed=False,
                reason="decision-critical evidence contains float values",
                metrics={"float_paths": float_paths},
            )
        return CheckerResult(checker_name=self.checker_name, passed=True)


def _find_float_paths(value: Any, path: str) -> list[str]:
    if isinstance(value, float):
        suffix = "" if math.isfinite(value) else " (non-finite)"
        return [f"{path}{suffix}"]
    if isinstance(value, dict):
        found: list[str] = []
        for key, item in value.items():
            found.extend(_find_float_paths(item, f"{path}.{key}"))
        return found
    if isinstance(value, list):
        found = []
        for index, item in enumerate(value):
            found.extend(_find_float_paths(item, f"{path}[{index}]"))
        return found
    return []


def _action_intent_from_context(context: dict[str, Any]) -> ActionIntent | None:
    raw_intent = context.get("action_intent")
    if raw_intent is None:
        return None
    if isinstance(raw_intent, ActionIntent):
        return raw_intent
    if isinstance(raw_intent, dict):
        return ActionIntent(**raw_intent)
    return None


def create_default_checkers() -> list[Checker]:
    return [
        CandidateSchemaChecker(),
        InputSetChecker(),
        EvidenceManifestChecker(),
        CandidateDigestChecker(),
        DeclaredToolsChecker(),
        DeterministicBoundaryChecker(),
        ResourceCapChecker(),
    ]
