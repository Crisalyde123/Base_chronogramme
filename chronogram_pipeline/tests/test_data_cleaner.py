import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data_cleaner import clean_data, unmerge_cells, standardize_and_clean


def test_clean_data_removes_noise():
    df = pd.DataFrame(
        [
            ["H1", "H2", "Empty"],
            ["val1", "val2", ""],
            ["TOTAL", "", ""],
            ["phase 1", "", ""],
            [None, None, None],
        ]
    )

    out = clean_data(df, chrono_rank=2)

    # Header row is kept; first data row numbered L001
    assert out.shape[0] == 2
    assert list(out["numero"]) == ["L001", "L002"]


def test_unmerge_cells_series_forward_fill():
    raw = pd.DataFrame({
        "A": ["val1", None, None],
        "B": [None, None, "val2"],
    })

    # Call directly on a Series to emulate intermediate processing
    series_input = raw.loc[0]
    out = unmerge_cells(series_input)
    assert isinstance(out, pd.DataFrame)
    # Horizontal propagation should duplicate the value on the row
    assert list(out.iloc[0]) == ["val1", "val1"]


def test_standardize_and_clean_nominal():
    df = pd.DataFrame(
        {
            "phase": [1],
            "statut": ["joué"],
            "type": ["structurant"],
            "horodatage": ["21/02/2024 09:30"],
            "emetteur": ["A"],
            "recepteur": ["B"],
            "nature": ["mail"],
            "resume": ["r"],
            "contenu": ["c"],
            "actions_attendues": ["a"],
            "commentaires": [""],
        }
    )

    out = standardize_and_clean(df, chrono_rank=3)
    assert out["id_chronogramme"].iloc[0] == "C003"
    assert out["numero"].iloc[0] == "L001"
    assert out["horodatage"].iloc[0] == "2024-02-21T09:30:00"


def test_standardize_and_clean_drop_repeated():
    df = pd.DataFrame({
        "phase": [1, "Texte"],
        "statut": ["joué", "Texte"],
        "type": ["structurant", "Texte"],
        "horodatage": ["21/02/2024 09:30", "Texte"],
        "emetteur": ["A", "Texte"],
        "recepteur": ["B", "Texte"],
        "nature": ["mail", "Texte"],
        "resume": ["r", "Texte"],
        "contenu": ["c", "Texte"],
        "actions_attendues": ["a", "Texte"],
        "commentaires": ["", "Texte"],
    })
    out = standardize_and_clean(df)
    assert out.shape[0] == 1


def test_standardize_and_clean_invalid_value():
    df = pd.DataFrame({"statut": ["invalid"]})
    out = standardize_and_clean(df)
    assert pd.isna(out["statut"].iloc[0])

