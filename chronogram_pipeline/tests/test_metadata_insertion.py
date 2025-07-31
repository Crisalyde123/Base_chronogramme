import sys
from pathlib import Path
import sqlite3

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.db_utils import insert_chronogram_metadata


def test_insert_chronogram_metadata(tmp_path):
    db_path = tmp_path / "chronos.db"
    metadata = {
        "nom_chronogramme": "Exercice Test",
        "date_exercice": "2024-01-01",
        "lieu_exercice": "Lyon",
        "etablissement_nom": "CHU",
        "etablissement_type": "Hopital",
        "submitter": "Bob",
        "nom_fichier_excel": "Chronogramme_CHU_Test_2024.xlsx",
        "nb_injects": 5,
    }
    chrono_id = insert_chronogram_metadata(metadata, db_path=db_path)
    assert isinstance(chrono_id, int)

    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "SELECT nom_chronogramme, date_exercice, fichier_source, nb_injects FROM Chronogrammes WHERE id_chronogramme=?",
            (chrono_id,),
        )
        row = cur.fetchone()

    assert row == (
        "Exercice Test",
        "2024-01-01",
        "Chronogramme_CHU_Test_2024.xlsx",
        5,
    )
