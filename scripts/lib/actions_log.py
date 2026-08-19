"""
Acoes (actions_log) para rollback.

Toda acao destrutiva do auto_classifier (adicionar musica em playlist,
criar playlist, remover musica) e registrada aqui. O rollback.py usa
esse log para desfazer operacoes.
"""
import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).parent
DATA_DIR = HERE.parent.parent / "data"
DB_PATH = DATA_DIR / "actions_log.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id        TEXT PRIMARY KEY,
    started_at    REAL,
    finished_at   REAL,
    command       TEXT,
    status        TEXT,
    summary       TEXT
);
CREATE TABLE IF NOT EXISTS actions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id        TEXT NOT NULL,
    ts            REAL,
    kind          TEXT,
    payload       TEXT,
    rolled_back   INTEGER DEFAULT 0
);
"""


@contextmanager
def _connect():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_PATH))
    con.row_factory = sqlite3.Row
    try:
        con.executescript(SCHEMA)
        yield con
        con.commit()
    finally:
        con.close()


def start_run(run_id: str, command: str):
    with _connect() as con:
        con.execute(
            "INSERT INTO runs (run_id, started_at, command, status) VALUES (?, ?, ?, ?)",
            (run_id, time.time(), command, "running"),
        )


def finish_run(run_id: str, status: str, summary: dict):
    with _connect() as con:
        con.execute(
            "UPDATE runs SET finished_at = ?, status = ?, summary = ? WHERE run_id = ?",
            (time.time(), status, json.dumps(summary, ensure_ascii=False), run_id),
        )


def log_action(run_id: str, kind: str, payload: dict):
    with _connect() as con:
        con.execute(
            "INSERT INTO actions (run_id, ts, kind, payload) VALUES (?, ?, ?, ?)",
            (run_id, time.time(), kind, json.dumps(payload, ensure_ascii=False)),
        )


def list_runs(limit: int = 20) -> list[dict]:
    with _connect() as con:
        rows = con.execute(
            "SELECT * FROM runs ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_run(run_id: str) -> dict | None:
    with _connect() as con:
        r = con.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
        return dict(r) if r else None


def get_actions(run_id: str, only_active: bool = True) -> list[dict]:
    with _connect() as con:
        q = "SELECT * FROM actions WHERE run_id = ?"
        if only_active:
            q += " AND rolled_back = 0"
        q += " ORDER BY id DESC"
        rows = con.execute(q, (run_id,)).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["payload"] = json.loads(d["payload"])
            out.append(d)
        return out


def mark_rolled_back(action_id: int):
    with _connect() as con:
        con.execute("UPDATE actions SET rolled_back = 1 WHERE id = ?", (action_id,))


def mark_run_status(run_id: str, status: str):
    with _connect() as con:
        con.execute("UPDATE runs SET status = ? WHERE run_id = ?", (status, run_id))
