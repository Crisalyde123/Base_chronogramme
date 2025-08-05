import sys
import sqlite3
from pathlib import Path

import pandas as pd
import openpyxl

# allow imports from project root and package
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "chronogram_pipeline"))
sys.path.insert(0, str(REPO_ROOT))

from src.excel_parser import detect_main_sheet
from src.manual_table_extractor import detect_header_row, detect_last_data_row
from src.db_utils import insert_chronogram_metadata, insert_injects

INPUTS_DIR = REPO_ROOT / "chronogram_pipeline" / "data" / "inputs"
METADATA_CSV = REPO_ROOT / "metadata.csv"


def _completion_for_table(conn: sqlite3.Connection, table: str, exclude: set[str]):
    """Return completion ratios for ``table`` excluding columns in ``exclude``."""
    conn.row_factory = sqlite3.Row
    cur = conn.execute(f"SELECT * FROM {table}")
    rows = cur.fetchall()
    completions = []
    for row in rows:
        record = dict(row)
        columns = [c for c in record if c not in exclude]
        total = len(columns)
        non_null = sum(record[c] not in (None, "") for c in columns)
        completions.append(non_null / total if total else 1.0)
    return completions


def _extract_table(xlsx_path: Path) -> pd.DataFrame:
    """Parse *xlsx_path* and return a DataFrame of the main table."""
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb[detect_main_sheet(xlsx_path)]
    lines = [list(row) for row in ws.iter_rows(values_only=True)]
    header_idx = detect_header_row(lines)
    last_idx = detect_last_data_row(lines, header_idx)
    header = lines[header_idx]
    data = lines[header_idx + 1 : last_idx + 1]
    df = pd.DataFrame(data, columns=header)
    df.dropna(how="all", inplace=True)
    rename_map = {
        "N°": "id_inject",
        "Heure": "horodatage",
        "Emeteur": "emetteur",
        "Récepteur": "recepteur",
        "Vecteur": "modalite",
        "Descriptif": "description",
        "Réaction attendues": "observations",
    }
    df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns}, inplace=True)
    if "horodatage" in df.columns:
        df["horodatage"] = df["horodatage"].astype(str)
    if "id_inject" in df.columns:
        df["id_inject"] = df["id_inject"].astype(str)
    return df


def test_db_completion_from_excel(tmp_path):
    file_name = "Kit intermédiaire.xlsx"
    xlsx_path = INPUTS_DIR / file_name
    df = _extract_table(xlsx_path)

    metadata_df = pd.read_csv(METADATA_CSV)
    metadata = metadata_df[metadata_df["nom_fichier"] == file_name].iloc[0].to_dict()
    metadata["nom_fichier_excel"] = file_name

    db_path = tmp_path / "chrono.db"
    chrono_id = insert_chronogram_metadata(metadata, db_path=db_path)

    df = df.dropna(subset=["id_inject"])
    df = df[~df["id_inject"].duplicated()]
    df["id_chronogramme"] = chrono_id
    df["etablissement_nom"] = metadata["etablissement_nom"]
    df["etablissement_type"] = metadata["etablissement_type"]
    insert_injects(df, db_path=db_path)

    with sqlite3.connect(db_path) as conn:
        chrono_comp = _completion_for_table(conn, "Chronogrammes", {"id_chronogramme"})
        inject_comp = _completion_for_table(conn, "Injects", {"id_chronogramme", "id_inject"})

    assert len(chrono_comp) == 1
    assert len(inject_comp) == len(df)
    assert all(0 <= r <= 1 for r in chrono_comp + inject_comp)

