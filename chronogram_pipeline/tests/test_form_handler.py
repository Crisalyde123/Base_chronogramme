import sqlite3
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import db_utils
from src.form_handler import handle_form_submission, save_excel_file


def test_handle_form_submission_saves_and_inserts(tmp_path, monkeypatch):
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
        "nom_chronogramme": "Test",
        "etablissement_nom": "Hopitâl de Lyon",
        "date_exercice": "2025/07/31",
        "file_path": str(src_file),
    }

    chrono_id, dest_path = handle_form_submission(form_data)

    assert src_file.exists()
    assert Path(dest_path).exists()
    assert chrono_id == 1

    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "SELECT nom_chronogramme, fichier_source FROM Chronogrammes WHERE id_chronogramme=?",
            (chrono_id,),
        )
        row = cur.fetchone()
    assert row == ("Test", dest_path)


def test_save_excel_file_generates_structured_name(tmp_path):
    src = tmp_path / "tempo.xlsx"
    src.write_text("data")

    dest = save_excel_file(
        src,
        "CHU Lyon",
        "Exo Feu",
        "2025-07-31",
        inputs_dir=tmp_path,
    )

    assert dest.name.startswith("Chronogramme_chu_lyon_exo_feu_2025-07-31")
    assert dest.exists()


def test_save_excel_file_rejects_non_xlsx(tmp_path):
    src = tmp_path / "tempo.xls"
    src.write_text("data")

    with pytest.raises(ValueError):
        save_excel_file(src, "A", "B", "2023-01-01", inputs_dir=tmp_path)
