-- OAWM beta storage hardening.
-- SQLiteStorage.initialize() creates this table automatically.

CREATE TABLE IF NOT EXISTS memory_revisions (
    revision_seq INTEGER PRIMARY KEY AUTOINCREMENT,
    revision_id TEXT NOT NULL UNIQUE,
    memory_id TEXT NOT NULL,
    update_id TEXT NOT NULL,
    content_digest TEXT NOT NULL,
    operation TEXT NOT NULL,
    before_lane TEXT,
    after_lane TEXT NOT NULL,
    receipt_id TEXT,
    event_id TEXT,
    raw_json TEXT NOT NULL
);
