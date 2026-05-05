"""Receipt verification port."""

from __future__ import annotations

from typing import Any, Protocol

from observable_agent_workflow_memory.core.models import (
    CheckerResult,
    EvidenceManifest,
    PromotionReceipt,
)


class ReceiptVerifier(Protocol):
    verifier_name: str

    def verify_receipt(
        self,
        receipt: PromotionReceipt,
        evidence: EvidenceManifest,
        context: dict[str, Any],
    ) -> CheckerResult:
        """Verify an existing receipt against evidence and execution context."""
