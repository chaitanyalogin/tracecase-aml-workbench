"""Local, append-only application history. No enterprise audit-integrity claim."""
import copy
import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


def db_path():
    return Path(os.getenv("TRACECASE_DB", str(Path(__file__).parent / "runtime/decisions.sqlite3")))


def connection():
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, case_id TEXT NOT NULL, created_at TEXT NOT NULL, payload TEXT NOT NULL)")
    return db


def save_decision(case_id, payload, *, session=None):
    if session is not None:
        events = session.setdefault("events", [])
        event_id = len(events) + 1
        events.append({**copy.deepcopy(payload), "id": event_id, "case_id": case_id,
                       "created_at": datetime.now(timezone.utc).isoformat()})
        return event_id
    with closing(connection()) as db, db:
        result = db.execute("INSERT INTO events(case_id,created_at,payload) VALUES(?,?,?)",
                            (case_id, datetime.now(timezone.utc).isoformat(), json.dumps(payload)))
        return result.lastrowid


def history(case_id, *, session=None):
    if session is not None:
        return copy.deepcopy([event for event in reversed(session.get("events", []))
                              if event["case_id"] == case_id])
    with closing(connection()) as db, db:
        rows = db.execute("SELECT id,created_at,payload FROM events WHERE case_id=? ORDER BY id DESC", (case_id,)).fetchall()
    return [{"id": r[0], "created_at": r[1], **json.loads(r[2])} for r in rows]
