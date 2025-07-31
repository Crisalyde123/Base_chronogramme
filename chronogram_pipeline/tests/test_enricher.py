import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.enricher import enrich_data


def test_enrich_data_generates_ids(tmp_path):
    df = pd.DataFrame({"Contenu": ["A", "B"]})

    out = enrich_data(
        df,
        id_chronogramme=1,
        etablissement_nom="CHU",
        etablissement_type="Hopital",
        nom_chronogramme="Test",
        date_exercice="2024-01-01",
    )

    assert list(out["numero_inject"]) == [1, 2]
    assert list(out["nb_injects"].unique()) == [2]
    assert (out["id_chronogramme"] == 1).all()
    assert (out["etablissement_nom"] == "CHU").all()
    assert (out["etablissement_type"] == "Hopital").all()


def test_enrich_data_completes_missing_ids(tmp_path):
    df = pd.DataFrame({"ID_inject": ["A", None, "", "B"]})

    out = enrich_data(
        df,
        id_chronogramme=2,
        etablissement_nom="CH",
        etablissement_type="Centre",
        nom_chronogramme="Demo",
        date_exercice="2025-01-01",
    )

    assert out["ID_inject"].tolist() == ["A", 1, 2, "B"]
    assert list(out["nb_injects"].unique()) == [4]

