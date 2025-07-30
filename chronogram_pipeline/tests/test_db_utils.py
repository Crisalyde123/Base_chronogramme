import sys
from pathlib import Path
import sqlite3

# allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.db_utils import init_databases


def table_exists(db_path: Path, table: str) -> bool:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        )
        return cur.fetchone() is not None


def test_init_databases_creates_tables(tmp_path):
    chrono_db = tmp_path / "chronogrammes.db"
    injects_db = tmp_path / "injects.db"
    init_databases(chrono_db, injects_db)

    assert chrono_db.exists()
    assert injects_db.exists()
    assert table_exists(chrono_db, "Chronogrammes")
    assert table_exists(injects_db, "Injects")
