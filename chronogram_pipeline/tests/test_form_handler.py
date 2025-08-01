import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import form_handler


def test_save_excel_file(tmp_path):
    src = tmp_path / "upload.xlsx"
    src.write_text("dummy")

    dest = form_handler.save_excel_file(
        src=src,
        etablissement_nom="H\u00f4pital G\u00e9n\u00e9ral",
        nom_chronogramme="Chrono D\u00e9mo",
        date_exercice="2024-02-01",
        inputs_dir=tmp_path,
    )

    assert dest.exists()
    assert dest.parent == tmp_path
    assert dest.read_text() == "dummy"
    assert dest.name == "Chronogramme_hopital_general_chrono_demo_2024-02-01.xlsx"


def test_handle_form_submission_saves_and_inserts(tmp_path, monkeypatch):
    db_path = tmp_path / "chronos.db"
    inputs_dir = tmp_path / "inputs"

    monkeypatch.setattr(form_handler, "DEFAULT_DB", db_path)

    orig_save = form_handler.save_excel_file

    def custom_save(src, etablissement_nom, nom_chronogramme, date_exercice):
        return orig_save(
            src,
            etablissement_nom,
            nom_chronogramme,
            date_exercice,
            inputs_dir=inputs_dir,
        )

    monkeypatch.setattr(form_handler, "save_excel_file", custom_save)

    src = tmp_path / "src.xlsx"
    src.write_text("dummy")

    form_data = {
        "file_path": str(src),
        "etablissement_nom": "\u00c9tablissement D\u00e9mo",
        "nom_chronogramme": "Plan A/B",
        "date_exercice": "01/02/2024",
    }

    chrono_id, dest = form_handler.handle_form_submission(form_data.copy())

    dest_path = Path(dest)
    assert isinstance(chrono_id, str)
    assert dest_path.exists()
    assert dest_path.parent == inputs_dir
    assert dest_path.name == "Chronogramme_etablissement_demo_plan_a_b_2024-02-01.xlsx"

    with sqlite3.connect(db_path) as conn:
        row = conn.execute(
            "SELECT id_chronogramme, fichier_source FROM Chronogrammes"
        ).fetchone()

    assert row == (chrono_id, str(dest_path))
