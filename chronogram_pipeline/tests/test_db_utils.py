import sys
from pathlib import Path
import sqlite3

# allow imports from project root and package
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "chronogram_pipeline"))
sys.path.insert(0, str(REPO_ROOT))

from src.db_utils import init_databases
from chronogram_pipeline.src import init_db


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


def test_init_db_main_creates_files(tmp_path, monkeypatch):
    out_dir = tmp_path / "databases"
    monkeypatch.setenv("OUTPUT_DB_PATH", str(out_dir))
    init_db.main()
    files = {f.name for f in out_dir.glob("*.db")}
    assert "chronogrammes.db" in files
    assert "injects.db" in files
