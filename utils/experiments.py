"""Historique distinct : ne mélange jamais modèles réels et simulateur."""
import json
from utils.storage import connect

def connection():
    db = connect()
    db.execute("CREATE TABLE IF NOT EXISTS experiments (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
    return db

def save_experiment(record):
    with connection() as db:
        db.execute("INSERT INTO experiments VALUES (?, ?)", (record["id"], json.dumps(record, ensure_ascii=False)))

def experiments():
    with connection() as db:
        rows = db.execute("SELECT payload FROM experiments ORDER BY rowid DESC").fetchall()
    return [json.loads(row[0]) for row in rows]

def review(identifier, decision, note):
    if decision not in ("non évalué", "conforme", "incorrect", "absent", "incertain"):
        raise ValueError("Évaluation inconnue")
    from datetime import datetime, timezone
    with connection() as db:
        row = db.execute("SELECT payload FROM experiments WHERE id=?", (identifier,)).fetchone()
        if row is None:
            raise ValueError("Expérience inconnue")
        record = json.loads(row[0])
        record.update(human_review=decision, review_note=note, reviewed_utc=datetime.now(timezone.utc).isoformat())
        db.execute("UPDATE experiments SET payload=? WHERE id=?", (json.dumps(record, ensure_ascii=False), identifier))
