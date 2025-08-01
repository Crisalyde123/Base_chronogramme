import sys
from pathlib import Path
import sqlite3
from openpyxl import Workbook
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import run_pipeline


def test_run_pipeline_skips_empty(tmp_path):
    xlsx = tmp_path / "empty.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.append(["Horodatage", "Description", "Emetteur"])
    wb.save(xlsx)

    db_path = tmp_path / "db.sqlite"
    log_dir = tmp_path / "logs"

    with pytest.raises(StopIteration):
        run_pipeline(xlsx, db_path=db_path, log_dir=log_dir)

    with sqlite3.connect(db_path) as conn:
        cur = conn.execute("SELECT COUNT(*) FROM Chronogrammes")
        count_chrono = cur.fetchone()[0]
    assert count_chrono == 0

