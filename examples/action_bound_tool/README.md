# Action-Bound Tool Example

This example uses the mock provider and an in-process tool. It demonstrates the
strict v0.1.0 beta rule: an external-effect tool call needs an `ActionIntent`
and a passing receipt bound to that exact action.

```powershell
uv run python examples/action_bound_tool/run_demo.py
```

The demo does not write files or call a network service. The tool is marked as
`external_effect=True` so the ActionGate path is exercised without requiring an
unsafe side effect.
