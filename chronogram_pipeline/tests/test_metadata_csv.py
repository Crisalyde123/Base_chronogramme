import sqlite3
from pathlib import Path
from openpyxl import Workbook
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import run_pipeline


def test_run_pipeline_uses_metadata_csv(tmp_path):
    xlsx = tmp_path / "test.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.append(["Horodatage", "Description", "Emetteur"])
    ws.append(["T0", "Desc", "A"])
    wb.save(xlsx)

    metadata_csv = tmp_path / "meta.csv"
    metadata_csv.write_text(
        "nom_fichier,nom_chronogramme,date_exercice,lieu_exercice,etablissement_nom,etablissement_type,submitter\n"
        f"{xlsx.name},Test Chrono,2025-01-01,Paris,Hopital X,CHU,test@example.com\n",
        encoding="utf-8",
    )

    db_path = tmp_path / "db.sqlite"
    log_dir = tmp_path / "logs"

    result = run_pipeline(xlsx, db_path=db_path, log_dir=log_dir, metadata_csv=metadata_csv)
    chrono_id = result["chrono_id"]

    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            "SELECT nom_chronogramme, date_exercice, lieu_exercice, etablissement_nom, etablissement_type, submitter FROM Chronogrammes WHERE id_chronogramme=?",
            (chrono_id,),
        )
        row = cur.fetchone()

    assert row == (
        "Test Chrono",
        "2025-01-01",
        "Paris",
        "Hopital X",
        "CHU",
        "test@example.com",
    )
