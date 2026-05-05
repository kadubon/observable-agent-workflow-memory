# Custom Proposer Plugin Example

`WorkflowProposer` lets applications replace the deterministic baseline proposal
logic while keeping storage, verification, retrieval, and promotion unchanged.

Minimal entry point:

```toml
[project.entry-points."oawm.proposers"]
domain = "my_package.proposer:create_proposer"
```

The example implementation is in `custom_proposer.py`. It can be copied into a
separate package and validated with the public tests for the surrounding ports.
