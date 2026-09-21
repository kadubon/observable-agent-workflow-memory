-- Explicit opt-in Store.initialize(); legacy schema 1.1 bytes remain unchanged.
CREATE TABLE IF NOT EXISTS receiver_events (
    seq INTEGER PRIMARY KEY,
    id TEXT NOT NULL UNIQUE,
    raw_json TEXT NOT NULL
);
