"""
Day 4 - #VoiceForBharat - Health Access track
SQLite memory store for callers.

Record shape (per the Day 4 spec):
{
    "user_id": "string",
    "name": "string",
    "language_preference": "string",
    "facts": { "age_band": ..., "ongoing_conditions": ..., "last_triage_outcome": ... },
    "last_interaction": "timestamp"
}

Health Access guardrail: we deliberately only ever store SHORT LABELS for
facts (e.g. "diabetes", "escalated") - never full written-out medical notes.
"""

import sqlite3
import json
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "callers.db")

# The only fact keys we allow to be stored for the Health Access track.
ALLOWED_FACT_KEYS = {"age_band", "ongoing_conditions", "last_triage_outcome"}


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS callers (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            language_preference TEXT,
            facts TEXT,
            last_interaction TEXT
        )
    """)
    conn.commit()
    conn.close()


def _row_to_dict(row):
    if not row:
        return None
    return {
        "user_id": row["user_id"],
        "name": row["name"],
        "language_preference": row["language_preference"],
        "facts": json.loads(row["facts"]) if row["facts"] else {},
        "last_interaction": row["last_interaction"],
    }


def get_caller(user_id):
    """Look up a caller by user_id. Returns None if unknown."""
    if not user_id:
        return None
    conn = _get_conn()
    row = conn.execute("SELECT * FROM callers WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return _row_to_dict(row)


def upsert_caller(user_id, name=None, language_preference=None, facts=None):
    """Save/merge what we just learned about this caller. `facts` is merged
    on top of any existing facts (new values overwrite old ones for the
    same key). Only ALLOWED_FACT_KEYS are ever persisted."""
    existing = get_caller(user_id) or {}
    merged_facts = dict(existing.get("facts", {}))

    if facts:
        for key, value in facts.items():
            if key in ALLOWED_FACT_KEYS and value:
                merged_facts[key] = value

    name = name or existing.get("name")
    language_preference = language_preference or existing.get("language_preference")

    conn = _get_conn()
    conn.execute("""
        INSERT INTO callers (user_id, name, language_preference, facts, last_interaction)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            name = excluded.name,
            language_preference = excluded.language_preference,
            facts = excluded.facts,
            last_interaction = excluded.last_interaction
    """, (
        user_id,
        name,
        language_preference,
        json.dumps(merged_facts),
        datetime.now(timezone.utc).isoformat(),
    ))
    conn.commit()
    conn.close()
    return get_caller(user_id)


def touch_last_interaction(user_id):
    """Update last_interaction without changing any stored facts (called on
    every connect, even if nothing new was learned)."""
    existing = get_caller(user_id)
    if not existing:
        return
    conn = _get_conn()
    conn.execute(
        "UPDATE callers SET last_interaction = ? WHERE user_id = ?",
        (datetime.now(timezone.utc).isoformat(), user_id),
    )
    conn.commit()
    conn.close()
