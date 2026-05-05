# ADR 0001: Ports and Adapters

Decision: core domain logic is independent of provider SDKs, storage backends,
retrieval engines, and CLI frameworks.

Rationale: the repository should be easy to fork and extend. Concrete
integrations are adapters. Public protocols are the compatibility surface.

