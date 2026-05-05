"""Default receipt verifier."""

from __future__ import annotations

from typing import Any

from observable_agent_workflow_memory.core.models import (
    CheckerResult,
    EvidenceManifest,
    MemoryRecord,
    PromotionReceipt,
)


class DefaultReceiptVerifier:
    verifier_name = "default-receipt"

    def verify_receipt(
        self,
        receipt: PromotionReceipt,
        evidence: EvidenceManifest,
        context: dict[str, Any],
    ) -> CheckerResult:
        candidate = context.get("candidate")
        if not isinstance(candidate, MemoryRecord):
            return CheckerResult(
                checker_name=self.verifier_name,
                passed=False,
                reason="receipt verification requires candidate context",
            )
        if receipt.candidate_id != candidate.memory_id:
            return CheckerResult(
                checker_name=self.verifier_name,
                passed=False,
                reason="receipt candidate_id does not match candidate",
            )
        if receipt.candidate_update_id != candidate.update_id:
            return CheckerResult(
                checker_name=self.verifier_name,
                passed=False,
                reason="receipt candidate_update_id does not match current candidate",
            )
        if evidence.candidate_id != receipt.candidate_id:
            return CheckerResult(
                checker_name=self.verifier_name,
                passed=False,
                reason="manifest candidate_id does not match receipt",
            )
        if evidence.candidate_update_id != receipt.candidate_update_id:
            return CheckerResult(
                checker_name=self.verifier_name,
                passed=False,
                reason="manifest candidate_update_id does not match receipt",
            )
        if evidence.manifest_id not in receipt.evidence_refs:
            return CheckerResult(
                checker_name=self.verifier_name,
                passed=False,
                reason="receipt does not reference evidence manifest",
            )
        has_bound_action_ref = (
            receipt.bound_action_id is not None and receipt.bound_action_id in receipt.evidence_refs
        )
        if receipt.bound_action_id is not None and not has_bound_action_ref:
            return CheckerResult(
                checker_name=self.verifier_name,
                passed=False,
                reason="receipt does not reference bound action id",
            )
        expected_digest = PromotionReceipt.compute_receipt_digest(
            candidate_id=receipt.candidate_id,
            candidate_update_id=receipt.candidate_update_id,
            bound_action_id=receipt.bound_action_id,
            profile=receipt.profile,
            checks=receipt.checks,
            result=receipt.result,
            evidence_refs=receipt.evidence_refs,
        )
        if receipt.receipt_digest != expected_digest:
            return CheckerResult(
                checker_name=self.verifier_name,
                passed=False,
                reason="receipt_digest mismatch",
                metrics={"expected": expected_digest, "observed": receipt.receipt_digest},
            )
        return CheckerResult(checker_name=self.verifier_name, passed=True)


def create_verifier() -> DefaultReceiptVerifier:
    return DefaultReceiptVerifier()
