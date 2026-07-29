import sqlite3

from app.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    interval_seconds REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS job_runs (
    id INTEGER PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    ran_at TEXT NOT NULL,
    node_id TEXT NOT NULL,
    fencing_token INTEGER
);

CREATE TABLE IF NOT EXISTS leader_state (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    highest_fencing_token_seen INTEGER NOT NULL DEFAULT 0
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db() -> None:
    conn = get_connection()
    try:
        conn.executescript(SCHEMA)
        conn.execute(
            "INSERT OR IGNORE INTO leader_state (id, highest_fencing_token_seen) VALUES (1, 0)"
        )
        conn.commit()
    finally:
        conn.close()


def get_or_create_job(name: str, interval_seconds: float) -> int:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO jobs (name, interval_seconds) VALUES (?, ?)",
            (name, interval_seconds),
        )
        conn.commit()
        row = conn.execute("SELECT id FROM jobs WHERE name = ?", (name,)).fetchone()
        return row[0]
    finally:
        conn.close()


def record_job_run(job_id: int, ran_at: str, node_id: str, fencing_token: int | None) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO job_runs (job_id, ran_at, node_id, fencing_token) VALUES (?, ?, ?, ?)",
            (job_id, ran_at, node_id, fencing_token),
        )
        conn.commit()
    finally:
        conn.close()
