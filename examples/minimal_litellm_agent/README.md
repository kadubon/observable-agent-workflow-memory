# Minimal LiteLLM Agent

```powershell
uv run oawm init
uv run oawm observe examples/minimal_litellm_agent/sample_events.jsonl --run-id demo
uv run oawm propose --run-id demo
uv run oawm verify <candidate-id>
uv run oawm promote <candidate-id>
uv run oawm run --model openai/gpt-4o-mini "Use certified memory only."
```

