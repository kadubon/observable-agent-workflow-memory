"""Optional finite comparison delegated to ALT; no OAWM optimizer."""

from __future__ import annotations

from typing import Any

from .native import reconstruct, runtime
from .wire import Cost, Qualification, digest


def compare(q: Qualification, now: int, transfer: str = "10", limit: int = 16) -> dict[str, Any]:
    reconstruct(q, now)
    transfer_cost = Cost(id="model-transfer", stage="transfer", amount=transfer)
    wire = runtime("alt_foundry_kernel.reuse.wire")
    model = runtime("alt_foundry_kernel.reuse.contracts")
    planner = runtime("alt_foundry_kernel.reuse.planning")
    checker = runtime("alt_foundry_kernel.reuse.checker")
    costs = [
        {
            "id": c.id,
            "stage": "checking" if c.stage == "verification" else c.stage,
            "unit": c.unit,
            "amount": c.amount,
            "allocations": {q.context.receiver: c.amount},
        }
        for c in [*q.costs, transfer_cost]
    ]
    for name, amount in (("scratch", "5"), ("reuse", "1")):
        costs.append(
            {
                "id": name,
                "stage": "execution",
                "unit": "work-unit",
                "amount": amount,
                "allocations": {q.context.receiver: amount},
            }
        )
    offer = dict(q.offer)
    offer["inputs"] = [wire.digest(q.context.inputs[0])]
    options = []
    for name in ("scratch", "reuse"):
        options.append(
            {
                "id": name,
                "kind": name,
                "prerequisites": [],
                "offer": "qualified" if name == "reuse" else None,
                "opportunities": ["local-use"],
                "costs": [name] + ([transfer_cost.id] if name == "reuse" else []),
                "occupancy": [{"resource": "verifier", "slot": 0, "quantity": 1}],
                "start": 0,
                "end": 1,
                "succeeds": {"finite": True},
                "hazard_cleared": True,
                "conflicts": [],
            }
        )
    contract = model.Contract.model_validate(
        {
            "version": "alt_reuse_contract_v1",
            "scope": q.context.mission,
            "study": q.context.workspace,
            "split": "training",
            "checkpoint": now,
            "evidence_cutoff": now,
            "initial_revision": digest(q),
            "time_origin": q.context.clock,
            "slot_seconds": "1",
            "horizon": 2,
            "valuation": offer["valuation"],
            "value_unit": "work-unit",
            "cost_rates": {"work-unit": "1"},
            "budgets": {"work-unit": "1000"},
            "capacities": {"verifier": 1},
            "scenarios": ["finite"],
            "opportunities": [
                {
                    "id": "local-use",
                    "receiver": q.context.receiver,
                    "context": q.context.context,
                    "input_digest": wire.digest(q.context.inputs[0]),
                    "task_family": q.context.task_family,
                    "task": "normalize-task",
                    "quality": offer["quality"],
                    "estimand": offer["estimand"],
                    "deadline": 2,
                    "required": True,
                    "value": {"finite": "10"},
                }
            ],
            "options": options,
            "bundles": [],
            "qualifications": [
                {
                    "id": "qualified",
                    "request": q.formation,
                    "candidate": q.candidate,
                    "offer": offer,
                }
            ],
            "costs": costs,
            "sunk_cost_ids": [c.id for c in q.costs],
            "objective": "worst-net-value-then-cost",
            "joint_model": "registered-separable-opportunities",
            "expansion_limit": limit,
            "execution_authority": None,
        }
    )
    plans = planner.compare(contract)
    for plan in plans.values():
        if plan.score is not None:
            checker.check_plan(contract, plan)
    return {
        "contract": contract.model_dump(),
        "plans": {k: v.model_dump() for k, v in plans.items()},
        "technical_eligibility": True,
        "economic_basis": "declared finite cost model",
        "empirical_benefit": None,
        "execution_authority": None,
    }
