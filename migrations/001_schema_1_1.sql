-- OAWM schema 1.1.
-- Runtime migrations are executed by SQLiteStorage.initialize().
-- This file documents the public storage shape for operators and downstream adapters.

PRAGMA user_version = 11;

-- promotion_receipts and evidence_manifests are append-only in 1.1.
-- Implementations should preserve insertion order with receipt_seq / manifest_seq.

-- memory_records is a current-value index. memory_revisions is the append-only
-- audit trail for memory state changes.
