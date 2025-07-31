import sqlite3
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import db_utils
from src.form_handler import handle_form_submission


def test_handle_form_submission_moves_and_inserts(tmp_path, monkeypatch):
    db_path = tmp_path / "chronogrammes.db"
    monkeypatch.setattr(db_utils, "DEFAULT_DB", db_path)
    monkeypatch.setattr("src.form_handler.DEFAULT_DB", db_path)
    monkeypatch.setattr("src.form_handler.INPUTS_DIR", tmp_path / "inputs")

    conn = db_utils.create_connection(db_path)
    db_utils.init_tables(conn)
    conn.close()

    src_file = tmp_path / "upload.xlsx"
    src_file.write_text("data")

    form_data = {
        "nom_chronogramme": "Feuvre Sec",
        "etablissement_nom": "CHU Bordeaux",
        "date_exercice": "2025-09",
        "file_path": str(src_file),
    }

    chrono_id, dest_path = handle_form_submission(form_data)

    assert not src_file.exists()
    assert Path(dest_path).exists()
    assert chrono_id == 1
    assert Path(dest_path).name.startswith(
        "Chronogramme_CHU_Bordeaux_Feuvre_Sec_2025-09"
    )

    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "SELECT nom_chronogramme, fichier_source FROM Chronogrammes WHERE id_chronogramme=?",
            (chrono_id,),
        )
        row = cur.fetchone()
    assert row == ("Feuvre Sec", dest_path)


def test_handle_form_submission_rejects_non_xlsx(tmp_path, monkeypatch):
    db_path = tmp_path / "chronogrammes.db"
    monkeypatch.setattr(db_utils, "DEFAULT_DB", db_path)
    monkeypatch.setattr("src.form_handler.DEFAULT_DB", db_path)
    monkeypatch.setattr("src.form_handler.INPUTS_DIR", tmp_path / "inputs")

    conn = db_utils.create_connection(db_path)
    db_utils.init_tables(conn)
    conn.close()

    src_file = tmp_path / "upload.txt"
    src_file.write_text("data")

    form_data = {
        "nom_chronogramme": "Test",
        "file_path": str(src_file),
    }

    with pytest.raises(ValueError):
        handle_form_submission(form_data)

