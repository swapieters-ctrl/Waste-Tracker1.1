import sqlite3
from datetime import datetime, date
import config


def get_conn():
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS registraties (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                datum       DATE    NOT NULL,
                tijdstip    DATETIME NOT NULL,
                telefoon    TEXT    NOT NULL,
                productnaam TEXT    NOT NULL,
                variant     TEXT    NOT NULL DEFAULT 'normaal',
                kilo        REAL    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS gesprek_status (
                telefoon        TEXT PRIMARY KEY,
                fase            TEXT NOT NULL DEFAULT 'idle',
                productnaam_ai  TEXT,
                variant_ai      TEXT,
                foto_url        TEXT
            );
        """)


# ── Registraties ──────────────────────────────────────────────────────────────

def sla_registratie_op(telefoon: str, productnaam: str, variant: str, kilo: float):
    nu = datetime.now()
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO registraties (datum, tijdstip, telefoon, productnaam, variant, kilo)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (nu.date().isoformat(), nu.strftime("%Y-%m-%d %H:%M:%S"), telefoon, productnaam, variant, kilo),
        )


def haal_registraties_op(van: date, tot: date) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT datum, tijdstip, telefoon, productnaam, variant, kilo
               FROM registraties
               WHERE datum BETWEEN ? AND ?
               ORDER BY tijdstip""",
            (van.isoformat(), tot.isoformat()),
        ).fetchall()
    return [dict(r) for r in rows]


# ── Gespreksstatus ────────────────────────────────────────────────────────────

def haal_status_op(telefoon: str) -> dict:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM gesprek_status WHERE telefoon = ?", (telefoon,)
        ).fetchone()
    if row:
        return dict(row)
    return {"telefoon": telefoon, "fase": "idle", "productnaam_ai": None, "variant_ai": None, "foto_url": None}


def sla_status_op(telefoon: str, fase: str, productnaam_ai: str = None,
                  variant_ai: str = None, foto_url: str = None):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO gesprek_status (telefoon, fase, productnaam_ai, variant_ai, foto_url)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(telefoon) DO UPDATE SET
                   fase           = excluded.fase,
                   productnaam_ai = excluded.productnaam_ai,
                   variant_ai     = excluded.variant_ai,
                   foto_url       = excluded.foto_url""",
            (telefoon, fase, productnaam_ai, variant_ai, foto_url),
        )


def reset_status(telefoon: str):
    sla_status_op(telefoon, "idle")
