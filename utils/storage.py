import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

DEFAULT_DB = Path(__file__).resolve().parents[1] / "data" / "history.sqlite3"

def connect():
    path = Path(os.environ.get("BRECHIA_DB", DEFAULT_DB))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    db.execute("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, created TEXT, payload TEXT)")
    return db

def save(results):
    run_id = str(uuid4())
    with connect() as db:
        db.execute("INSERT INTO runs VALUES (?, ?, ?)",
                   (run_id, datetime.now(timezone.utc).isoformat(), json.dumps(results, ensure_ascii=False)))
    return run_id

def history():
    with connect() as db:
        rows = db.execute("SELECT id, created, payload FROM runs ORDER BY created DESC").fetchall()
    return [{"id": r[0], "date_utc": r[1], "résultats": json.loads(r[2])} for r in rows]


def reset_history():
    """Efface uniquement les expériences, dans une transaction SQLite."""
    with connect() as db:
        db.execute("DELETE FROM runs")
