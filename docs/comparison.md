# Comparison

OAWM is a workflow-memory verification kernel. It governs when memory becomes
admissible for reuse. It is not a general agent framework, vector memory store,
or truth-certification system.

| Project family | Primary strength | OAWM difference |
| --- | --- | --- |
| Letta / MemGPT | Long-lived agent state and memory management. | OAWM focuses on evidence-bound promotion from raw traces to verified workflow contracts. |
| LangGraph / LangMem | Graph orchestration, persistence, and agent state. | OAWM is framework-neutral and governs admissibility independent of graph runtime. |
| Mem0 | Application memory extraction and recall. | OAWM treats extracted memories as candidates until evidence manifests and receipts pass. |
| Zep | Conversation memory, user context, and retrieval. | OAWM prioritizes audit lanes, receipt binding, and fail-closed promotion over general recall. |
| LlamaIndex | Data connectors, indexing, and RAG pipelines. | OAWM can use retrieval, but its core unit is a certified workflow memory, not an index hit. |
| CrewAI | Multi-agent task orchestration. | OAWM does not orchestrate teams; it supplies admissible workflow memory to runtimes. |
| Reflexion | Verbal reflection for iterative improvement. | OAWM stores reflections as raw/candidate memory until deterministic checks promote them. |
| Voyager | Skill discovery and code-based agent learning. | OAWM requires skill/workflow reuse to carry receipts, declared tools, and resource caps. |
| Generative Agents | Believable agent behavior from memory streams. | OAWM is less concerned with behavioral richness and more with replayable admissibility. |

The practical distinction is narrow: OAWM answers whether a memory is allowed to
be reused under declared evidence and checks. It does not answer whether the
memory is globally true, whether a model will follow it, or whether a tool is
sandboxed safely.
