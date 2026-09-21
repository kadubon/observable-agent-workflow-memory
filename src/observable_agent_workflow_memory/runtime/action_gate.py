"""Fail-closed action gate."""

from __future__ import annotations

from observable_agent_workflow_memory.core.canonical import digest_json
from observable_agent_workflow_memory.core.errors import FailClosedError
from observable_agent_workflow_memory.core.models import ActionIntent, PromotionReceipt


class ActionGate:
    """Gate external effects on action-bound passing receipts."""

    def __init__(self, *, strict: bool = True) -> None:
        self.strict = strict

    def ensure_allowed(
        self,
        *,
        external_effects: bool,
        receipts: list[PromotionReceipt] | None = None,
        intent: ActionIntent | None = None,
        reason: str = "",
    ) -> None:
        if not external_effects:
            return
        if not self.strict:
            return
        if intent is None:
            detail = reason or "external effects require an action intent"
            raise FailClosedError(detail)
        if not receipts:
            detail = reason or "external effects require action-bound passing receipts"
            raise FailClosedError(detail)
        seed = {
            "tool_name": intent.tool_name,
            "effect_class": intent.effect_class,
            "args_digest": intent.args_digest,
            "resource_caps": intent.resource_caps,
        }
        if intent.action_id != "act_" + digest_json(seed)[:32]:
            raise FailClosedError("action intent identity does not bind its current fields")
        for receipt in receipts:
            if (
                receipt.result != "passed"
                or not receipt.checks
                or any(not c.passed for c in receipt.checks)
            ):
                detail = reason or f"receipt did not pass: {receipt.receipt_id}"
                raise FailClosedError(detail)
        if intent.required_receipt_id is not None:
            matching = [
                receipt for receipt in receipts if receipt.receipt_id == intent.required_receipt_id
            ]
            if not matching:
                detail = reason or "required receipt was not supplied"
                raise FailClosedError(detail)
            receipts = matching
        if any(receipt.bound_action_id == intent.action_id for receipt in receipts):
            return
        detail = reason or "external effects require a receipt bound to this action intent"
        raise FailClosedError(detail)
