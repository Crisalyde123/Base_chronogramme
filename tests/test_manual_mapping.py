import sys
from pathlib import Path
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "chronogram_pipeline"))
sys.path.insert(0, str(REPO_ROOT))

from src.data_cleaner import (
    load_column_mapping,
    load_value_mapping,
    _append_new_columns,
    _append_new_values,
)


def test_load_column_mapping_purge(tmp_path):
    csv = tmp_path / "colonnes.csv"
    pd.DataFrame(
        [
            {"chronogramme": "C1", "raw_name": "A", "mapped_name": "X"},
            {"chronogramme": "C1", "raw_name": "B", "mapped_name": "phase"},
            {"chronogramme": "C1", "raw_name": "C", "mapped_name": ""},
        ]
    ).to_csv(csv, index=False)
    history = tmp_path / "hist.csv"
    mapping = load_column_mapping(csv, history_file=history)
    assert mapping == {"B": "phase", "C": "__DROP__"}
    remaining = pd.read_csv(csv)
    assert list(remaining["raw_name"]) == ["A"]
    hist = pd.read_csv(history)
    assert len(hist) == 2


def test_load_value_mapping_purge(tmp_path):
    csv = tmp_path / "valeurs.csv"
    pd.DataFrame(
        [
            {
                "chronogramme": "C1",
                "column_name": "phase",
                "raw_value": "X",
                "mapped_value": "1",
            },
            {
                "chronogramme": "C1",
                "column_name": "statut",
                "raw_value": "old",
                "mapped_value": "X",
            },
            {
                "chronogramme": "C1",
                "column_name": "phase",
                "raw_value": "y",
                "mapped_value": "__EMPTY__",
            },
        ]
    ).to_csv(csv, index=False)
    history = tmp_path / "hist_val.csv"
    mapping = load_value_mapping(csv, history_file=history)
    assert mapping == {"phase": {"X": "1", "y": ""}}
    remaining = pd.read_csv(csv)
    assert len(remaining) == 1
    assert remaining.iloc[0]["raw_value"] == "old"
    hist = pd.read_csv(history)
    assert len(hist) == 2


def test_append_functions_no_duplicates(tmp_path):
    col_csv = tmp_path / "cols.csv"
    _append_new_columns(col_csv, "C1", ["A", "B"])
    _append_new_columns(col_csv, "C2", ["A", "C"])
    df = pd.read_csv(col_csv)
    assert set(df["raw_name"]) == {"A", "B", "C"}

    val_csv = tmp_path / "vals.csv"
    _append_new_values(val_csv, "C1", [("col", "1"), ("col", "2")])
    _append_new_values(val_csv, "C2", [("col", "1")])
    dfv = pd.read_csv(val_csv)
    assert len(dfv) == 2
