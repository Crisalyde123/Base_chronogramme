from .logger import get_logger
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

logger = get_logger(__name__)

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB = BASE_DIR / "output/databases/chronogrammes.db"

CHRONO_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS Chronogrammes (
    id_chronogramme INTEGER PRIMARY KEY,
    nom_chronogramme TEXT NOT NULL,
    date_exercice TEXT,
    lieu_exercice TEXT,
    etablissement_nom TEXT,
    etablissement_type TEXT,
    submitter TEXT,
    date_soumission TEXT,
    fichier_source TEXT,
    nb_injects INTEGER
);
"""

INJECTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS Injects (
    id_inject_global INTEGER PRIMARY KEY,
    id_chronogramme INTEGER NOT NULL,
    id_inject TEXT,
    horodatage TEXT,
    description TEXT,
    emetteur TEXT,
    destinataire TEXT,
    type_inject TEXT,
    modalite TEXT,
    phase_exercice TEXT,
    observations TEXT,
    etablissement_nom TEXT,
    etablissement_type TEXT,
    FOREIGN KEY(id_chronogramme) REFERENCES Chronogrammes(id_chronogramme),
    UNIQUE(id_chronogramme, id_inject)
);
"""

def create_connection(db_path: Path) -> sqlite3.Connection:
    """Create a SQLite connection enabling foreign keys."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_tables(conn: sqlite3.Connection) -> None:
    """Create Chronogrammes and Injects tables."""
    logger.debug("Creating Chronogrammes table")
    conn.execute(CHRONO_TABLE_SQL)
    logger.debug("Creating Injects table")
    conn.execute(INJECTS_TABLE_SQL)
    conn.commit()


def init_databases(chronogram_db: Path, injects_db: Path) -> None:
    """Create both SQLite databases with required tables."""
    logger.info("Initialising databases")
    with create_connection(chronogram_db) as chrono_conn:
        init_tables(chrono_conn)
    if injects_db != chronogram_db:
        with create_connection(injects_db) as inject_conn:
            init_tables(inject_conn)
    logger.info("Databases initialised: %s, %s", chronogram_db, injects_db)


def insert_chronogram(record: Dict[str, Any], db_path: Path | None = None) -> int:
    """Insert a chronogram record and return its generated ID."""
    db_path = db_path or DEFAULT_DB
    with create_connection(db_path) as conn:
        init_tables(conn)
        columns = [
            "nom_chronogramme",
            "date_exercice",
            "lieu_exercice",
            "etablissement_nom",
            "etablissement_type",
            "submitter",
            "date_soumission",
            "fichier_source",
            "nb_injects",
        ]
        values = [record.get(col) for col in columns]
        placeholders = ", ".join("?" for _ in columns)
        sql = f"INSERT INTO Chronogrammes ({', '.join(columns)}) VALUES ({placeholders})"
        cur = conn.execute(sql, values)
        conn.commit()
        chrono_id = int(cur.lastrowid)
        logger.debug("Inserted chronogram with id %s", chrono_id)
        return chrono_id
