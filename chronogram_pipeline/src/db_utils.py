from .logger import get_logger
import sqlite3
from pathlib import Path

logger = get_logger(__name__)

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
