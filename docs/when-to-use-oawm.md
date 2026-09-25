# When to use OAWM

Observable Agent Workflow Memory (OAWM) governs evidence-bound procedural reuse.
Use it when a workflow needs explicit promotion and inspectable lifecycle decisions;
opt into receiver qualification when exact inputs, dependencies and current receiver
eligibility matter. A script or ordinary memory store is often sufficient when these
boundaries add no value. OAWM does not replace RAG, a vector database or tool isolation.

The maintained [When to use OAWM guide](wiki/When-to-Use-OAWM.md) explains these
choices and host responsibilities. Start from the [README](../README.md), then
[Getting Started](wiki/Getting-Started.md) or the authoritative
[security model](security_model.md) and [receiver contract](receiver-qualified-memory.md).
