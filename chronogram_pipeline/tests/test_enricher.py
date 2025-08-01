import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.enricher import enrich_data


def test_enrich_data_generates_ids(tmp_path):
    df = pd.DataFrame({"Contenu": ["A", "B"]})

    out = enrich_data(
        df,
        id_chronogramme="C001",
        etablissement_nom="CHU",
        etablissement_type="Hopital",
        nom_chronogramme="Test",
        date_exercice="2024-01-01",
    )

    assert list(out["numero"]) == [1, 2]
    assert out["id_inject"].tolist() == ["C001_L001", "C001_L002"]
    assert list(out["nb_injects"].unique()) == [2]
    assert (out["id_chronogramme"] == "C001").all()
    assert (out["etablissement_nom"] == "CHU").all()
    assert (out["etablissement_type"] == "Hopital").all()


def test_enrich_data_completes_missing_ids(tmp_path):
    df = pd.DataFrame({"ID_inject": ["A", None, "", "B"]})

    out = enrich_data(
        df,
        id_chronogramme="C002",
        etablissement_nom="CH",
        etablissement_type="Centre",
        nom_chronogramme="Demo",
        date_exercice="2025-01-01",
    )

    assert list(out["numero"]) == [1, 2, 3, 4]
    assert out["id_inject"].tolist() == [
        "C002_L001",
        "C002_L002",
        "C002_L003",
        "C002_L004",
    ]
    assert list(out["nb_injects"].unique()) == [4]


def test_enrich_data_preserves_input():
    df = pd.DataFrame({"numero": [5], "Contenu": ["A"]})
    df_copy = df.copy(deep=True)
    enrich_data(
        df,
        id_chronogramme="C003",
        etablissement_nom="E",
        etablissement_type="T",
        nom_chronogramme="N",
        date_exercice="2024",
    )
    assert df.equals(df_copy)
