import sys
from pathlib import Path

import pandas as pd
import openpyxl

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "chronogram_pipeline"))
sys.path.insert(0, str(REPO_ROOT))

from src.excel_parser import detect_main_sheet
from src.manual_table_extractor import detect_header_row, detect_last_data_row
from src.data_cleaner import (
    load_column_mapping,
    load_value_mapping,
    _append_new_columns,
    _append_new_values,
)

INPUTS_DIR = REPO_ROOT / "chronogram_pipeline" / "data" / "inputs"


def _extract_table(path: Path) -> tuple[pd.DataFrame, list[str]]:
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb[detect_main_sheet(path)]
    lines = [list(row) for row in ws.iter_rows(values_only=True)]
    header_idx = detect_header_row(lines)
    last_idx = detect_last_data_row(lines, header_idx)
    header = lines[header_idx]
    data = lines[header_idx + 1 : last_idx + 1]
    df = pd.DataFrame(data, columns=header)
    df.dropna(how="all", inplace=True)
    return df, header


def test_manual_mapping_from_excel(tmp_path):
    file_name = "Kit intermédiaire.xlsx"
    df, headers = _extract_table(INPUTS_DIR / file_name)

    headers = [h for h in headers if h is not None]

    col_csv = tmp_path / "cols.csv"
    hist_csv = tmp_path / "cols_hist.csv"
    _append_new_columns(col_csv, headers, file_name)
    _append_new_columns(col_csv, headers, file_name)
    mapping = load_column_mapping(col_csv, history_file=hist_csv)
    assert mapping == {}
    remaining_cols = pd.read_csv(col_csv)
    assert set(remaining_cols["raw_name"]) == set(headers)

    val_csv = tmp_path / "vals.csv"
    hist_val = tmp_path / "vals_hist.csv"
    values = []
    if "Vecteur" in df.columns:
        values = [("Vecteur", v) for v in df["Vecteur"].dropna().astype(str).unique().tolist()]
    _append_new_values(val_csv, values, file_name)
    _append_new_values(val_csv, values, file_name)
    val_mapping = load_value_mapping(val_csv, history_file=hist_val)
    assert val_mapping == {}
    remaining_vals = pd.read_csv(val_csv)
    assert len(remaining_vals) == len(values)

