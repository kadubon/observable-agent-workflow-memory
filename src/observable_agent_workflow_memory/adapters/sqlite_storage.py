"""SQLite storage adapter."""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from typing import Any

from observable_agent_workflow_memory.core.canonical import canonical_json, digest_json
from observable_agent_workflow_memory.core.errors import FailClosedError, NotFoundError
from observable_agent_workflow_memory.core.models import (
    Event,
    EvidenceManifest,
    Lane,
    MemoryOperation,
    MemoryRecord,
    MemoryRevision,
    PromotionReceipt,
    RetrievedMemory,
    StoredEvent,
    WorkflowContract,
    now_utc,
)


class SQLiteStorage:
    backend_name = "sqlite"

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con

    def initialize(self) -> None:
        with self._connect() as con:
            con.execute("PRAGMA journal_mode=WAL")
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    obs_seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    obs_time TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    payload_digest TEXT NOT NULL,
                    raw_json TEXT NOT NULL
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_records (
                    memory_id TEXT PRIMARY KEY,
                    lane TEXT NOT NULL,
                    claim TEXT NOT NULL,
                    workflow_contract_id TEXT,
                    receipt_id TEXT,
                    raw_json TEXT NOT NULL
                )
                """
            )
            con.execute(
                """
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
                )
                """
            )
            con.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
                    memory_id UNINDEXED,
                    lane UNINDEXED,
                    claim,
                    body,
                    tokenize='unicode61'
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_contracts (
                    contract_id TEXT PRIMARY KEY,
                    raw_json TEXT NOT NULL
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS promotion_receipts (
                    receipt_seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_id TEXT NOT NULL UNIQUE,
                    candidate_id TEXT NOT NULL,
                    candidate_update_id TEXT NOT NULL DEFAULT '',
                    result TEXT NOT NULL,
                    raw_json TEXT NOT NULL
                )
                """
            )
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS evidence_manifests (
                    manifest_seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    manifest_id TEXT NOT NULL,
                    candidate_id TEXT NOT NULL,
                    candidate_update_id TEXT NOT NULL DEFAULT '',
                    raw_json TEXT NOT NULL
                )
                """
            )
            self._migrate_append_only_tables(con)
            con.execute("CREATE INDEX IF NOT EXISTS idx_events_run_id ON events(run_id)")
            con.execute("CREATE INDEX IF NOT EXISTS idx_memory_lane ON memory_records(lane)")
            con.execute(
                "CREATE INDEX IF NOT EXISTS idx_memory_revisions_memory "
                "ON memory_revisions(memory_id, revision_seq)"
            )
            con.execute(
                "CREATE INDEX IF NOT EXISTS idx_receipts_candidate "
                "ON promotion_receipts(candidate_id)"
            )
            con.execute(
                "CREATE INDEX IF NOT EXISTS idx_manifests_candidate "
                "ON evidence_manifests(candidate_id)"
            )
            con.execute(
                "CREATE INDEX IF NOT EXISTS idx_manifests_id "
                "ON evidence_manifests(manifest_id)"
            )
            con.execute("PRAGMA user_version = 11")

    def _migrate_append_only_tables(self, con: sqlite3.Connection) -> None:
        receipt_columns = self._table_columns(con, "promotion_receipts")
        if receipt_columns and "receipt_seq" not in receipt_columns:
            con.execute("ALTER TABLE promotion_receipts RENAME TO promotion_receipts_v10")
            con.execute(
                """
                CREATE TABLE promotion_receipts (
                    receipt_seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_id TEXT NOT NULL UNIQUE,
                    candidate_id TEXT NOT NULL,
                    candidate_update_id TEXT NOT NULL DEFAULT '',
                    result TEXT NOT NULL,
                    raw_json TEXT NOT NULL
                )
                """
            )
            con.execute(
                """
                INSERT INTO promotion_receipts
                    (receipt_id, candidate_id, result, raw_json)
                SELECT receipt_id, candidate_id, result, raw_json
                FROM promotion_receipts_v10
                ORDER BY receipt_id ASC
                """
            )
            con.execute("DROP TABLE promotion_receipts_v10")

        manifest_columns = self._table_columns(con, "evidence_manifests")
        if manifest_columns and "manifest_seq" not in manifest_columns:
            con.execute("ALTER TABLE evidence_manifests RENAME TO evidence_manifests_v10")
            con.execute(
                """
                CREATE TABLE evidence_manifests (
                    manifest_seq INTEGER PRIMARY KEY AUTOINCREMENT,
                    manifest_id TEXT NOT NULL,
                    candidate_id TEXT NOT NULL,
                    candidate_update_id TEXT NOT NULL DEFAULT '',
                    raw_json TEXT NOT NULL
                )
                """
            )
            con.execute(
                """
                INSERT INTO evidence_manifests
                    (manifest_id, candidate_id, raw_json)
                SELECT manifest_id, candidate_id, raw_json
                FROM evidence_manifests_v10
                ORDER BY manifest_id ASC
                """
            )
            con.execute("DROP TABLE evidence_manifests_v10")

    @staticmethod
    def _table_columns(con: sqlite3.Connection, table_name: str) -> set[str]:
        rows = con.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {str(row["name"]) for row in rows}

    def append_event(self, event: Event) -> StoredEvent:
        observed_digest = digest_json(event.payload)
        if event.payload_digest != observed_digest:
            msg = "event payload_digest does not match canonical payload digest"
            raise FailClosedError(msg)
        obs_time = now_utc()
        raw = event.model_dump(mode="json")
        with self._connect() as con:
            con.execute(
                """
                INSERT INTO events (event_id, obs_time, run_id, kind, payload_digest, raw_json)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    obs_time.isoformat(),
                    event.run_id,
                    event.kind,
                    event.payload_digest,
                    canonical_json(raw),
                ),
            )
            obs_seq = int(con.execute("SELECT last_insert_rowid()").fetchone()[0])
        return StoredEvent(**raw, obs_seq=obs_seq, obs_time=obs_time, collector_seq=obs_seq)

    def list_events(
        self,
        *,
        run_id: str | None = None,
        limit: int | None = None,
    ) -> list[StoredEvent]:
        sql = "SELECT obs_seq, obs_time, raw_json FROM events"
        params: list[Any] = []
        if run_id is not None:
            sql += " WHERE run_id = ?"
            params.append(run_id)
        sql += " ORDER BY obs_seq ASC"
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        with self._connect() as con:
            rows = con.execute(sql, params).fetchall()
        events: list[StoredEvent] = []
        for row in rows:
            raw = json.loads(str(row["raw_json"]))
            obs_seq = int(row["obs_seq"])
            events.append(
                StoredEvent(
                    **raw,
                    obs_seq=obs_seq,
                    obs_time=row["obs_time"],
                    collector_seq=obs_seq,
                )
            )
        return events

    def get_event(self, event_id: str) -> StoredEvent:
        with self._connect() as con:
            row = con.execute(
                "SELECT obs_seq, obs_time, raw_json FROM events WHERE event_id = ?",
                (event_id,),
            ).fetchone()
        if row is None:
            raise NotFoundError(f"event not found: {event_id}")
        raw = json.loads(str(row["raw_json"]))
        obs_seq = int(row["obs_seq"])
        return StoredEvent(**raw, obs_seq=obs_seq, obs_time=row["obs_time"], collector_seq=obs_seq)

    def upsert_memory_record(
        self,
        record: MemoryRecord,
        *,
        operation: MemoryOperation = MemoryOperation.WRITE,
        reason: str = "",
        receipt_id: str | None = None,
        event_id: str | None = None,
    ) -> MemoryRecord:
        raw = record.model_dump(mode="json")
        body = canonical_json(
            {
                "claim": record.claim,
                "metadata": record.metadata,
                "source_event_ids": record.source_event_ids,
                "workflow_contract_id": record.workflow_contract_id,
                "receipt_id": record.receipt_id,
            }
        )
        with self._connect() as con:
            existing = con.execute(
                "SELECT lane FROM memory_records WHERE memory_id = ?",
                (record.memory_id,),
            ).fetchone()
            before_lane = Lane(str(existing["lane"])) if existing is not None else None
            con.execute(
                """
                INSERT INTO memory_records (
                    memory_id, lane, claim, workflow_contract_id, receipt_id, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(memory_id) DO UPDATE SET
                    lane=excluded.lane,
                    claim=excluded.claim,
                    workflow_contract_id=excluded.workflow_contract_id,
                    receipt_id=excluded.receipt_id,
                    raw_json=excluded.raw_json
                """,
                (
                    record.memory_id,
                    record.lane.value,
                    record.claim,
                    record.workflow_contract_id,
                    record.receipt_id,
                    canonical_json(raw),
                ),
            )
            revision = MemoryRevision.create(
                record=record,
                operation=operation,
                before_lane=before_lane,
                reason=reason,
                receipt_id=receipt_id or record.receipt_id,
                event_id=event_id,
            )
            con.execute(
                """
                INSERT INTO memory_revisions (
                    revision_id, memory_id, update_id, content_digest, operation,
                    before_lane, after_lane, receipt_id, event_id, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    revision.revision_id,
                    revision.memory_id,
                    revision.update_id,
                    revision.content_digest,
                    revision.operation.value,
                    revision.before_lane.value if revision.before_lane else None,
                    revision.after_lane.value,
                    revision.receipt_id,
                    revision.event_id,
                    canonical_json(revision),
                ),
            )
            con.execute("DELETE FROM memory_fts WHERE memory_id = ?", (record.memory_id,))
            con.execute(
                "INSERT INTO memory_fts (memory_id, lane, claim, body) VALUES (?, ?, ?, ?)",
                (record.memory_id, record.lane.value, record.claim, body),
            )
        return record

    def get_memory_record(self, memory_id: str) -> MemoryRecord:
        with self._connect() as con:
            row = con.execute(
                "SELECT raw_json FROM memory_records WHERE memory_id = ?", (memory_id,)
            ).fetchone()
        if row is None:
            raise NotFoundError(f"memory record not found: {memory_id}")
        return _memory_record_from_json(str(row["raw_json"]))

    def list_memory_records(self, *, lane: Lane | None = None) -> list[MemoryRecord]:
        sql = "SELECT raw_json FROM memory_records"
        params: list[Any] = []
        if lane is not None:
            sql += " WHERE lane = ?"
            params.append(lane.value)
        sql += " ORDER BY memory_id ASC"
        with self._connect() as con:
            rows = con.execute(sql, params).fetchall()
        return [_memory_record_from_json(str(row["raw_json"])) for row in rows]

    def list_memory_revisions(self, *, memory_id: str | None = None) -> list[MemoryRevision]:
        sql = "SELECT raw_json FROM memory_revisions"
        params: list[Any] = []
        if memory_id is not None:
            sql += " WHERE memory_id = ?"
            params.append(memory_id)
        sql += " ORDER BY revision_seq ASC"
        with self._connect() as con:
            rows = con.execute(sql, params).fetchall()
        return [MemoryRevision(**json.loads(str(row["raw_json"]))) for row in rows]

    def create_contract(self, contract: WorkflowContract) -> WorkflowContract:
        raw_json = canonical_json(contract)
        with self._connect() as con:
            existing = con.execute(
                "SELECT raw_json FROM workflow_contracts WHERE contract_id = ?",
                (contract.contract_id,),
            ).fetchone()
            if existing is not None:
                if str(existing["raw_json"]) != raw_json:
                    msg = f"workflow contract conflict for id: {contract.contract_id}"
                    raise FailClosedError(msg)
                return contract
            con.execute(
                """
                INSERT INTO workflow_contracts (contract_id, raw_json)
                VALUES (?, ?)
                """,
                (contract.contract_id, raw_json),
            )
        return contract

    def get_contract(self, contract_id: str) -> WorkflowContract:
        with self._connect() as con:
            row = con.execute(
                "SELECT raw_json FROM workflow_contracts WHERE contract_id = ?", (contract_id,)
            ).fetchone()
        if row is None:
            raise NotFoundError(f"workflow contract not found: {contract_id}")
        return WorkflowContract(**json.loads(str(row["raw_json"])))

    def create_receipt(self, receipt: PromotionReceipt) -> PromotionReceipt:
        with self._connect() as con:
            con.execute(
                """
                INSERT INTO promotion_receipts
                    (receipt_id, candidate_id, candidate_update_id, result, raw_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    receipt.receipt_id,
                    receipt.candidate_id,
                    receipt.candidate_update_id,
                    receipt.result,
                    canonical_json(receipt),
                ),
            )
        return receipt

    def get_receipt(self, receipt_id: str) -> PromotionReceipt:
        with self._connect() as con:
            row = con.execute(
                "SELECT raw_json FROM promotion_receipts WHERE receipt_id = ?", (receipt_id,)
            ).fetchone()
        if row is None:
            raise NotFoundError(f"receipt not found: {receipt_id}")
        return _receipt_from_json(str(row["raw_json"]))

    def list_receipts(self, *, candidate_id: str | None = None) -> list[PromotionReceipt]:
        sql = "SELECT raw_json FROM promotion_receipts"
        params: list[Any] = []
        if candidate_id is not None:
            sql += " WHERE candidate_id = ?"
            params.append(candidate_id)
        sql += " ORDER BY receipt_seq ASC"
        with self._connect() as con:
            rows = con.execute(sql, params).fetchall()
        return [_receipt_from_json(str(row["raw_json"])) for row in rows]

    def create_evidence_manifest(self, manifest: EvidenceManifest) -> EvidenceManifest:
        with self._connect() as con:
            con.execute(
                """
                INSERT INTO evidence_manifests
                    (manifest_id, candidate_id, candidate_update_id, raw_json)
                VALUES (?, ?, ?, ?)
                """,
                (
                    manifest.manifest_id,
                    manifest.candidate_id,
                    manifest.candidate_update_id,
                    canonical_json(manifest),
                ),
            )
        return manifest

    def get_evidence_manifest(self, manifest_id: str) -> EvidenceManifest:
        with self._connect() as con:
            row = con.execute(
                """
                SELECT raw_json FROM evidence_manifests
                WHERE manifest_id = ?
                ORDER BY manifest_seq DESC
                LIMIT 1
                """,
                (manifest_id,),
            ).fetchone()
        if row is None:
            raise NotFoundError(f"evidence manifest not found: {manifest_id}")
        return _manifest_from_json(str(row["raw_json"]))

    def audit_counts(self) -> dict[str, int]:
        with self._connect() as con:
            rows = con.execute(
                "SELECT lane, COUNT(*) AS n FROM memory_records GROUP BY lane ORDER BY lane"
            ).fetchall()
            event_count = int(con.execute("SELECT COUNT(*) FROM events").fetchone()[0])
            receipt_count = int(
                con.execute("SELECT COUNT(*) FROM promotion_receipts").fetchone()[0]
            )
            contract_count = int(
                con.execute("SELECT COUNT(*) FROM workflow_contracts").fetchone()[0]
            )
            manifest_count = int(
                con.execute("SELECT COUNT(*) FROM evidence_manifests").fetchone()[0]
            )
            revision_count = int(
                con.execute("SELECT COUNT(*) FROM memory_revisions").fetchone()[0]
            )
        counts = {str(row["lane"]): int(row["n"]) for row in rows}
        counts["events"] = event_count
        counts["receipts"] = receipt_count
        counts["contracts"] = contract_count
        counts["evidence_manifests"] = manifest_count
        counts["memory_revisions"] = revision_count
        return counts

    def search_memory(
        self,
        query: str,
        *,
        lane_filter: list[Lane],
        limit: int,
    ) -> list[RetrievedMemory]:
        lane_values = [lane.value for lane in lane_filter]
        if not lane_values:
            return []
        placeholders = ",".join("?" for _ in lane_values)
        params: list[Any] = [*lane_values]
        if query.strip():
            fts_query = _to_fts_query(query)
            sql = (
                "SELECT m.raw_json, bm25(memory_fts) AS score "
                "FROM memory_fts JOIN memory_records m ON m.memory_id = memory_fts.memory_id "
                f"WHERE memory_fts.lane IN ({placeholders}) AND memory_fts MATCH ? "
                "ORDER BY score LIMIT ?"
            )
            params.extend([fts_query, limit])
            try:
                with self._connect() as con:
                    rows = con.execute(sql, params).fetchall()
            except sqlite3.OperationalError:
                rows = self._search_like(query, lane_values, limit)
        else:
            sql = (
                "SELECT raw_json, 0.0 AS score FROM memory_records "
                f"WHERE lane IN ({placeholders}) LIMIT ?"
            )
            params.append(limit)
            with self._connect() as con:
                rows = con.execute(sql, params).fetchall()
        return [_row_to_retrieved(row) for row in rows]

    def _search_like(self, query: str, lane_values: list[str], limit: int) -> list[sqlite3.Row]:
        placeholders = ",".join("?" for _ in lane_values)
        like = f"%{query}%"
        sql = (
            "SELECT raw_json, 0.0 AS score FROM memory_records "
            f"WHERE lane IN ({placeholders}) AND claim LIKE ? LIMIT ?"
        )
        with self._connect() as con:
            return list(con.execute(sql, [*lane_values, like, limit]).fetchall())


def _row_to_retrieved(row: sqlite3.Row) -> RetrievedMemory:
    record = _memory_record_from_json(str(row["raw_json"]))
    raw_score = float(row["score"])
    score = -raw_score if raw_score < 0 else raw_score
    return RetrievedMemory(
        memory_id=record.memory_id,
        update_id=record.update_id,
        content_digest=record.content_digest(),
        lane=record.lane,
        claim=record.claim,
        score=score,
        workflow_contract_id=record.workflow_contract_id,
        receipt_id=record.receipt_id,
        source_event_ids=record.source_event_ids,
    )


def _memory_record_from_json(raw_json: str) -> MemoryRecord:
    raw = json.loads(raw_json)
    if "update_id" not in raw:
        content_seed = {
            "claim": raw["claim"],
            "source_event_ids": raw.get("source_event_ids", []),
            "metadata": raw.get("metadata", {}),
            "supersedes": raw.get("supersedes", []),
            "contradicts": raw.get("contradicts", []),
        }
        raw["update_id"] = MemoryRecord.compute_update_id(
            str(raw["memory_id"]),
            digest_json(content_seed),
        )
    return MemoryRecord(**raw)


def _receipt_from_json(raw_json: str) -> PromotionReceipt:
    raw = json.loads(raw_json)
    if "candidate_update_id" not in raw:
        raw["candidate_update_id"] = "upd_legacy"
    if "verification_id" not in raw:
        raw["verification_id"] = f"ver_legacy_{str(raw['receipt_id']).removeprefix('rcp_')}"
    if "receipt_digest" not in raw:
        raw["receipt_digest"] = digest_json(
            {
                "candidate_id": raw.get("candidate_id"),
                "candidate_update_id": raw.get("candidate_update_id"),
                "profile": raw.get("profile"),
                "checks": raw.get("checks", []),
                "result": raw.get("result"),
                "evidence_refs": raw.get("evidence_refs", []),
            }
        )
    raw.setdefault("bound_action_id", None)
    return PromotionReceipt(**raw)


def _manifest_from_json(raw_json: str) -> EvidenceManifest:
    raw = json.loads(raw_json)
    raw.setdefault("candidate_update_id", "upd_legacy")
    return EvidenceManifest(**raw)


def _to_fts_query(query: str) -> str:
    tokens = re.findall(r"[\w\-]+", query, flags=re.UNICODE)
    if not tokens:
        return '""'
    return " ".join(f'"{token.replace(chr(34), chr(34) + chr(34))}"' for token in tokens[:16])


def create_storage(path: str | Path = ".oawm/oawm.sqlite") -> SQLiteStorage:
    storage = SQLiteStorage(path)
    storage.initialize()
    return storage
