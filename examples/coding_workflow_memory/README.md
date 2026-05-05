# Coding Workflow Memory Example

Use raw coding logs as short-term memory, then promote only replayable workflow
steps into certified memory.

```powershell
uv run oawm observe examples/coding_workflow_memory/sample_coding_events.jsonl --run-id coding-demo
uv run oawm propose --run-id coding-demo
```

