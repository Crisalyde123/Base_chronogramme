import sys
import sqlite3
from pathlib import Path

import pandas as pd

# allow imports from project root and package
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "chronogram_pipeline"))
sys.path.insert(0, str(REPO_ROOT))

from src.db_utils import insert_chronogram_metadata, insert_injects

THRESHOLD = 0.4


def _completion_for_table(conn: sqlite3.Connection, table: str, exclude: set[str]):
    conn.row_factory = sqlite3.Row
    cur = conn.execute(f"SELECT * FROM {table}")
    rows = cur.fetchall()
    completions = []
    failures = []
    for idx, row in enumerate(rows):
        record = dict(row)
        columns = [c for c in record if c not in exclude]
        total = len(columns)
        non_null = sum(record[c] not in (None, "") for c in columns)
        ratio = non_null / total if total else 1.0
        completions.append(ratio)
        if ratio < THRESHOLD:
            empty_cols = [c for c in columns if record[c] in (None, "")]
            failures.append((idx, ratio, empty_cols))
    return completions, failures


def test_chronogram_completion(tmp_path):
    db_path = tmp_path / "chrono.db"
    metadata = {
        "nom_chronogramme": "Test Chrono",
        "date_exercice": "2024-01-01",
        "lieu_exercice": "Paris",
        "etablissement_nom": "CHU",
        "etablissement_type": "Hopital",
        "submitter": "UnitTest",
        "nom_fichier_excel": "dummy.xlsx",
    }
    insert_chronogram_metadata(metadata, db_path=db_path)

    with sqlite3.connect(db_path) as conn:
        _, failures = _completion_for_table(
            conn, "Chronogrammes", {"id_chronogramme"}
        )
    assert not failures, f"Incomplete chronogram rows: {failures}"


def test_injects_completion(tmp_path):
    db_path = tmp_path / "chrono.db"
    metadata = {
        "nom_chronogramme": "Test Chrono",
        "date_exercice": "2024-01-01",
        "lieu_exercice": "Paris",
        "etablissement_nom": "CHU",
        "etablissement_type": "Hopital",
        "submitter": "UnitTest",
        "nom_fichier_excel": "dummy.xlsx",
    }
    chrono_id = insert_chronogram_metadata(metadata, db_path=db_path)

    df = pd.DataFrame(
        {
            "id_chronogramme": [chrono_id, chrono_id],
            "id_inject": ["1", "2"],
            "horodatage": ["T0", "T1"],
            "description": ["desc", None],
            "emetteur": ["A", "B"],
            "recepteur": ["X", "Y"],
            "type_inject": ["Info", None],
            "modalite": [None, "SMS"],
            "phase_exercice": [None, None],
            "observations": ["", "note"],
            "etablissement_nom": ["CHU", "CHU"],
            "etablissement_type": ["Hopital", "Hopital"],
        }
    )
    insert_injects(df, db_path=db_path)

    with sqlite3.connect(db_path) as conn:
        _, failures = _completion_for_table(
            conn,
            "Injects",
            {"id_inject_global", "id_chronogramme", "id_inject"},
        )
    assert not failures, f"Incomplete inject rows: {failures}"
