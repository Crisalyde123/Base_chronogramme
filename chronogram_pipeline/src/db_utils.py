from .logger import get_logger
import sqlite3
import unicodedata
from datetime import datetime, date, timezone
from pathlib import Path
from typing import Dict, Any
import os
import pandas as pd
import shutil

logger = get_logger(__name__)

BASE_DIR = Path(__file__).resolve().parents[1]
DB_DIR = Path(os.getenv("OUTPUT_DB_PATH", BASE_DIR / "output/databases"))
DEFAULT_DB = DB_DIR / "chronogrammes.db"

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


def _clean_string(value: Any) -> str:
    """Return a trimmed ASCII representation of ``value``."""
    text = "" if value is None else str(value).strip()
    normalized = unicodedata.normalize("NFKD", text)
    return normalized.encode("ascii", "ignore").decode("ascii")


def _format_date(value: Any) -> str:
    """Return ``value`` formatted as ``YYYY-MM-DD`` when possible."""
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, str):
        value = value.strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
    return _clean_string(value)


def insert_chronogram_metadata(metadata: Dict[str, Any], db_path: Path | None = None) -> int:
    """Validate, clean and insert chronogram metadata.

    Parameters
    ----------
    metadata : Dict[str, Any]
        Raw metadata coming from the form submission.
    db_path : Path, optional
        SQLite database path. Defaults to ``DEFAULT_DB``.

    Returns
    -------
    int
        The generated ``id_chronogramme``.
    """

    required = [
        "nom_chronogramme",
        "date_exercice",
        "lieu_exercice",
        "etablissement_nom",
        "etablissement_type",
        "submitter",
        "nom_fichier_excel",
    ]
    missing = [field for field in required if not metadata.get(field)]
    if missing:
        raise ValueError(f"Missing required metadata fields: {', '.join(missing)}")

    record = {
        "nom_chronogramme": _clean_string(metadata["nom_chronogramme"]),
        "date_exercice": _format_date(metadata["date_exercice"]),
        "lieu_exercice": _clean_string(metadata["lieu_exercice"]),
        "etablissement_nom": _clean_string(metadata["etablissement_nom"]),
        "etablissement_type": _clean_string(metadata["etablissement_type"]),
        "submitter": _clean_string(metadata["submitter"]),
        "date_soumission": datetime.now(timezone.utc).isoformat(),
        "fichier_source": _clean_string(metadata["nom_fichier_excel"]),
        "nb_injects": int(metadata.get("nb_injects", 0) or 0),
    }

    return insert_chronogram(record, db_path=db_path)


def insert_injects(df, db_path: Path | None = None) -> int:
    """Insert multiple injects from DataFrame and return number inserted."""
    import pandas as pd

    if df is None or len(df) == 0:
        return 0
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

    db_path = db_path or DEFAULT_DB
    columns = [
        "id_chronogramme",
        "id_inject",
        "horodatage",
        "description",
        "emetteur",
        "destinataire",
        "type_inject",
        "modalite",
        "phase_exercice",
        "observations",
        "etablissement_nom",
        "etablissement_type",
    ]

    rows = []
    for _, row in df.iterrows():
        entry = [row.get(col) for col in columns]
        rows.append(entry)

    placeholders = ", ".join("?" for _ in columns)
    sql = f"INSERT INTO Injects ({', '.join(columns)}) VALUES ({placeholders})"

    with create_connection(db_path) as conn:
        init_tables(conn)
        conn.executemany(sql, rows)
        conn.commit()

    logger.info("Inserted %s injects", len(rows))
    return len(rows)


def delete_chronogram(id_chronogramme: int, db_path: Path | None = None) -> None:
    """Remove chronogram and related injects from the database."""
    db_path = db_path or DEFAULT_DB
    with create_connection(db_path) as conn:
        init_tables(conn)
        conn.execute(
            "DELETE FROM Injects WHERE id_chronogramme = ?",
            (id_chronogramme,),
        )
        conn.execute(
            "DELETE FROM Chronogrammes WHERE id_chronogramme = ?",
            (id_chronogramme,),
        )
        conn.commit()
    logger.warning("Deleted chronogram %s with no injects", id_chronogramme)


def update_chronogram_stats(id_chronogramme: int, df, db_path: Path | None = None) -> None:
    """Update nb_injects for a chronogram using DataFrame length."""
    import pandas as pd

    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")

    nb_injects = len(df)
    db_path = db_path or DEFAULT_DB
    with create_connection(db_path) as conn:
        init_tables(conn)
        conn.execute(
            "UPDATE Chronogrammes SET nb_injects = ? WHERE id_chronogramme = ?",
            (nb_injects, id_chronogramme),
        )
        conn.commit()
    logger.debug("Updated chronogram %s with %s injects", id_chronogramme, nb_injects)


def archive_file(
    file_path: Path,
    *,
    chrono_id: int | None = None,
    archive_dir: Path | None = None,
) -> Path:
    """Move ``file_path`` to the archive directory with a timestamped name.

    Parameters
    ----------
    file_path : Path
        Excel file that has been successfully processed.
    chrono_id : int, optional
        Chronogram identifier used to build the archive filename.
    archive_dir : Path, optional
        Destination directory. Defaults to ``data/archive/raw_excels`` in the
        project tree.

    Returns
    -------
    Path
        Location of the archived file.
    """

    if archive_dir is None:
        archive_dir = BASE_DIR / "data" / "archive" / "raw_excels"
    archive_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = file_path.suffix
    base = file_path.stem
    if chrono_id is not None:
        new_name = f"{base}_{chrono_id}_{timestamp}{suffix}"
    else:
        new_name = f"{base}_{timestamp}{suffix}"
    dest = archive_dir / new_name
    shutil.move(str(file_path), dest)
    logger.info("Archived %s to %s", file_path, dest)
    return dest

