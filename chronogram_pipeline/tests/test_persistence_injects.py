import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import sqlite3
import pandas as pd

from src.data_cleaner import clean_data
from src.db_utils import init_databases, insert_injects


def test_insert_two_injects_in_db(tmp_path):
    # Create minimal CSV with two injects
    csv_file = tmp_path / "chrono.csv"
    pd.DataFrame(
        {
            "Phase_exercice": ["1", "2"],
            "Type d'inject": ["Info", "Alerte"],
            "Horodatage": ["T0", "T1"],
            "Emetteur": ["A", "B"],
            "Destinataire": ["X", "Y"],
            "Modalite": ["Mail", "SMS"],
            "Descriptif": ["msg1", "msg2"],
            "Commentaires": ["", "note"],
        }
    ).to_csv(csv_file, index=False)

    # Extraction + nettoyage
    df_raw = pd.read_csv(csv_file)
    df_clean = clean_data(df_raw, chrono_rank=99)

    # Prepare DataFrame for DB insertion
    df_db = df_clean.head(2).copy()
    chrono_id = 99
    df_db["id_chronogramme"] = chrono_id
    df_db["description"] = df_db["resume"]
    df_db["modalite"] = df_db["nature"]
    df_db["type_inject"] = df_db["type"]
    df_db["phase_exercice"] = df_db["phase"]
    df_db["observations"] = df_db["commentaires"]
    df_db["etablissement_nom"] = "CHU Test"
    df_db["etablissement_type"] = "Hopital"

    # Initialise temporary databases
    db_dir = tmp_path / "db"
    chrono_db = db_dir / "chronogrammes.db"
    injects_db = db_dir / "injects.db"
    init_databases(chrono_db, injects_db)
    with sqlite3.connect(injects_db) as conn:
        conn.execute("INSERT INTO Chronogrammes (id_chronogramme, nom_chronogramme) VALUES (?, ?)", (chrono_id, "Test"))
        conn.commit()

    inserted = insert_injects(df_db, db_path=injects_db)
    assert inserted == 2

    # Query database
    with sqlite3.connect(injects_db) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM Injects WHERE id_chronogramme = ? ORDER BY id_inject",
            (chrono_id,),
        ).fetchall()

    assert len(rows) == 2
    for i, row in enumerate(rows):
        for col in [
            "id_chronogramme",
            "id_inject",
            "horodatage",
            "description",
            "emetteur",
            "recepteur",
            "type_inject",
            "modalite",
            "phase_exercice",
            "observations",
            "etablissement_nom",
            "etablissement_type",
        ]:
            assert row[col] == df_db.iloc[i][col]

