"""
Cache SQLite de generos musicais.

Evita repetir chamadas ao Last.fm para o mesmo artista/musica.
Armazena: artista, titulo (opcional), generos, tags, confianca, fonte.
"""
import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

HERE = Path(__file__).parent
DATA_DIR = HERE.parent.parent / "data"
DB_PATH = DATA_DIR / "genre_cache.db"


SCHEMA = """
CREATE TABLE IF NOT EXISTS genre_cache (
    key           TEXT PRIMARY KEY,
    artist        TEXT NOT NULL,
    title         TEXT,
    genres        TEXT,
    tags          TEXT,
    confidence    REAL,
    source        TEXT,
    listeners     INTEGER,
    fetched_at    REAL
);
CREATE INDEX IF NOT EXISTS idx_artist ON genre_cache(artist);
"""


def make_key(artist: str, title: str | None = None) -> str:
    artist_norm = (artist or "").strip().lower()
    if title:
        title_norm = title.strip().lower()
        return f"track::{artist_norm}::{title_norm}"
    return f"artist::{artist_norm}"


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


def get(artist: str, title: str | None = None, max_age_days: float = 90.0):
    key = make_key(artist, title)
    with _connect() as con:
        row = con.execute(
            "SELECT * FROM genre_cache WHERE key = ?", (key,)
        ).fetchone()
        if not row:
            return None
        age = time.time() - row["fetched_at"]
        if age > max_age_days * 86400:
            return None
        return dict(row)


def put(artist: str, title: str | None = None, *, genres=None, tags=None,
        confidence: float = 0.0, source: str = "", listeners: int = 0):
    key = make_key(artist, title)
    with _connect() as con:
        con.execute(
            """INSERT OR REPLACE INTO genre_cache
               (key, artist, title, genres, tags, confidence, source, listeners, fetched_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                key,
                artist,
                title,
                json.dumps(genres or [], ensure_ascii=False),
                json.dumps(tags or [], ensure_ascii=False),
                float(confidence),
                source,
                int(listeners),
                time.time(),
            ),
        )


def stats() -> dict:
    with _connect() as con:
        row = con.execute(
            "SELECT COUNT(*) AS total, SUM(CASE WHEN title IS NULL THEN 1 ELSE 0 END) AS artists, "
            "SUM(CASE WHEN title IS NOT NULL THEN 1 ELSE 0 END) AS tracks FROM genre_cache"
        ).fetchone()
        return {"total": row["total"], "artists": row["artists"], "tracks": row["tracks"]}


def invalidate(artist: str, title: str | None = None):
    key = make_key(artist, title)
    with _connect() as con:
        con.execute("DELETE FROM genre_cache WHERE key = ?", (key,))


def clear_all():
    with _connect() as con:
        con.execute("DELETE FROM genre_cache")


if __name__ == "__main__":
    print(f"DB: {DB_PATH}")
    print(stats())
