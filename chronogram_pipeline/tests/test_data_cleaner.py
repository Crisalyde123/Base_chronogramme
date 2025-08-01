import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data_cleaner import (
    clean_data,
    unmerge_cells,
    standardize_and_clean,
    load_column_mapping,
    load_value_mapping,
    drop_empty_rows,
    drop_empty_cols,
    remove_parasitic_rows,
    _validate_values,
)


def test_clean_data_removes_noise():
    df = pd.DataFrame([
        ["H1", "H2", "Empty"],
        ["val1", "val2", ""],
        ["TOTAL", "", ""],
        ["phase 1", "", ""],
        [None, None, None],
    ])

    out = clean_data(df, chrono_rank=2)
    # On garde l’entête + deux vraies lignes
    assert out.shape[0] == 2
    assert list(out["numero"]) == ["L001", "L002"]


def test_unmerge_cells_series_forward_fill():
    raw = pd.DataFrame({
        "A": ["val1", None, None],
        "B": [None, None, "val2"],
    })
    series_input = raw.loc[0]
    out = unmerge_cells(series_input)
    assert isinstance(out, pd.DataFrame)
    # La cellule A se réplique horizontalement
    assert list(out.iloc[0]) == ["val1", "val1"]


def test_standardize_and_clean_nominal():
    df = pd.DataFrame({
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
    })

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
    # La deuxième ligne répétitive doit être supprimée
    assert out.shape[0] == 1


def test_standardize_and_clean_invalid_value():
    df = pd.DataFrame({"statut": ["invalid"]})
    out = standardize_and_clean(df)
    # Une valeur non reconnue devient NaN
    assert pd.isna(out["statut"].iloc[0])


def test_no_total_line_loss():
    # Vérifie qu'on ne perd pas toutes les lignes quand la première ressemble à du bruit
    columns = [
        "phase", "statut", "type", "horodatage", "emetteur", "recepteur",
        "nature", "resume", "contenu", "actions_attendues", "commentaires"
    ]
    df = pd.DataFrame([
        ["Texte"] * len(columns),
        [1, "joué", "structurant", "21/02/2024", "A", "B", "mail", "r", "c", "a", ""],
    ], columns=columns)

    out = clean_data(df)
    assert not out.empty


# Helpers for mapping tests
def _create_column_file(path: Path, rows: list[tuple[str, str]]):
    pd.DataFrame(rows, columns=["raw_name", "mapped_name"]).to_csv(path, index=False)


def _create_value_file(path: Path, rows: list[tuple[str, str, str]]):
    pd.DataFrame(rows, columns=["column_name", "raw_value", "mapped_value"]).to_csv(path, index=False)


def test_load_mapping_and_clean(tmp_path):
    col_file = tmp_path / "colonnes.csv"
    val_file = tmp_path / "valeurs.csv"
    _create_column_file(col_file, [("A", "alpha"), ("B", "")])
    _create_value_file(val_file, [("alpha", "x", "X")])

    col_map = load_column_mapping(col_file)
    val_map = load_value_mapping(val_file)

    df = pd.DataFrame({"A": ["x"], "B": ["y"]})
    out = clean_data(
        df,
        chrono_rank=1,
        column_map=col_map,
        value_map=val_map,
        columns_file=col_file,
        values_file=val_file,
    )

    assert "alpha" in out.columns
    assert "B" not in out.columns
    assert out["alpha"].iloc[0] == "X"


def test_clean_data_new_column(tmp_path):
    col_file = tmp_path / "cols.csv"
    val_file = tmp_path / "vals.csv"
    _create_column_file(col_file, [])
    _create_value_file(val_file, [])
    col_map = load_column_mapping(col_file)
    val_map = load_value_mapping(val_file)

    df = pd.DataFrame({"Unknown": [1]})
    with pytest.raises(StopIteration):
        clean_data(
            df,
            column_map=col_map,
            value_map=val_map,
            columns_file=col_file,
            values_file=val_file,
        )

    # La colonne inconnue doit avoir été ajoutée dans cols.csv avec mapped_name "XXX"
    df_new = pd.read_csv(col_file)
    assert (df_new["raw_name"] == "Unknown").any()
    assert (df_new.loc[df_new["raw_name"] == "Unknown", "mapped_name"] == "XXX").any()


def test_clean_data_new_value(tmp_path):
    col_file = tmp_path / "c.csv"
    val_file = tmp_path / "v.csv"
    _create_column_file(col_file, [("A", "alpha")])
    _create_value_file(val_file, [("alpha", "bar", "BAR")])
    col_map = load_column_mapping(col_file)
    val_map = load_value_mapping(val_file)

    df = pd.DataFrame({"A": ["foo"]})
    with pytest.raises(StopIteration):
        clean_data(
            df,
            column_map=col_map,
            value_map=val_map,
            columns_file=col_file,
            values_file=val_file,
        )

    # La nouvelle valeur brute "foo" doit avoir été enregistrée avec "XXX"
    df_new = pd.read_csv(val_file)
    values = set(df_new.itertuples(index=False, name=None))
    assert ("alpha", "foo", "XXX") in values


def test_drop_empty_rows_cols_and_parasitic():
    df = pd.DataFrame(
        {
            "A": ["", None, "data"],
            "B": [None, None, ""],
            "C": ["TOTAL", "phase 1", "x"],
        }
    )
    out = drop_empty_rows(df)
    out = drop_empty_cols(out)
    out = remove_parasitic_rows(out)
    assert list(out.columns) == ["A", "C"]
    assert out.shape[0] == 1
    assert out.iloc[0]["C"] == "x"


def test_validate_values_normalizes(tmp_path):
    df = pd.DataFrame(
        {
            "phase": ["1", "cinq"],
            "statut": ["Joue", "inval"],
            "type": ["Structurant", "foo"],
            "nature": ["SMS", "Oral"],
            "horodatage": ["01/02/2024 08:00", "bad"],
        }
    )
    _validate_values(df)
    assert list(df["phase"]) == ["1", pd.NA]
    assert list(df["statut"]) == ["joué", pd.NA]
    assert list(df["type"]) == ["structurant", pd.NA]
    assert list(df["nature"]) == ["SMS", "oral"]
    assert df["horodatage"].iloc[0] == "2024-02-01T08:00:00"
    assert pd.isna(df["horodatage"].iloc[1])
