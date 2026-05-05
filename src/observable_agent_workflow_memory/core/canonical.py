"""Canonical JSON and digest helpers."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
from enum import Enum
from typing import Any

from pydantic import BaseModel


def normalize_for_json(value: Any) -> Any:
    """Return a JSON-compatible value with deterministic representation."""

    if isinstance(value, BaseModel):
        return normalize_for_json(value.model_dump(mode="json", exclude_none=False))
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dt.datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=dt.UTC)
        return value.astimezone(dt.UTC).replace(microsecond=0).isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    if isinstance(value, float):
        if not math.isfinite(value):
            msg = "non-finite floats are not canonical JSON"
            raise ValueError(msg)
        return value
    if isinstance(value, dict):
        return {str(k): normalize_for_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize_for_json(v) for v in value]
    if isinstance(value, set):
        return sorted(normalize_for_json(v) for v in value)
    return value


def canonical_json(value: Any) -> str:
    """Serialize as stable, compact JSON."""

    return json.dumps(
        normalize_for_json(value),
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def canonical_bytes(value: Any) -> bytes:
    return canonical_json(value).encode("utf-8")


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def digest_json(value: Any) -> str:
    return sha256_hex(canonical_bytes(value))
