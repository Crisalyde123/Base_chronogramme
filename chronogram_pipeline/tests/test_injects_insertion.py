import sys
from pathlib import Path
import pandas as pd
import sqlite3

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.db_utils import (
    insert_chronogram_metadata,
    insert_injects,
    update_chronogram_stats,
)


def test_insert_injects_and_update_stats(tmp_path):
    db_path = tmp_path / "chronos.db"
    metadata = {
        "nom_chronogramme": "Exercice Test",
        "date_exercice": "2024-01-01",
        "lieu_exercice": "Paris",
        "etablissement_nom": "CHU",
        "etablissement_type": "Hopital",
        "submitter": "Alice",
        "nom_fichier_excel": "Chrono.xlsx",
    }

    chrono_id = insert_chronogram_metadata(metadata, db_path=db_path)

    df = pd.DataFrame({
        "id_inject": [1, 2, 3, 4, 5],
        "horodatage": ["T0", "T1", "T2", "T3", "T4"],
        "description": ["a", "b", "c", "d", "e"],
        "emetteur": ["X"] * 5,
        "destinataire": ["Y"] * 5,
        "type_inject": ["Info"] * 5,
        "modalite": ["Mail"] * 5,
        "phase_exercice": ["P"] * 5,
        "observations": [""] * 5,
        "id_chronogramme": [chrono_id] * 5,
        "etablissement_nom": [metadata["etablissement_nom"]] * 5,
        "etablissement_type": [metadata["etablissement_type"]] * 5,
    })

    inserted = insert_injects(df, db_path=db_path)
    assert inserted == 5

    update_chronogram_stats(chrono_id, df, db_path=db_path)

    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "SELECT COUNT(*) FROM Injects WHERE id_chronogramme=?",
            (chrono_id,),
        )
        count = cur.fetchone()[0]
        cur = conn.execute(
            "SELECT nb_injects FROM Chronogrammes WHERE id_chronogramme=?",
            (chrono_id,),
        )
        nb = cur.fetchone()[0]

    assert count == 5
    assert nb == 5
