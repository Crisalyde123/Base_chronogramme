from pathlib import Path
import shutil
import pandas as pd

from src.mapping_utils import update_mapping_headers


def test_update_mapping_headers(tmp_path):
    source_dir = Path(__file__).resolve().parents[1] / "data" / "inputs"
    inputs_dir = tmp_path / "inputs"
    inputs_dir.mkdir()
    for name in ["Chronogramme.xlsx", "Chronogramme sur mesure.xlsx"]:
        shutil.copy(source_dir / name, inputs_dir / name)
    mapping_csv = tmp_path / "mapping_headers.csv"

    # prepopulate with one known header
    df = pd.DataFrame([["L", ""]], columns=["En-tête original", "En-tête standard"])
    df.to_csv(mapping_csv, index=False)

    total, new_added = update_mapping_headers(inputs_dir, mapping_csv, max_files=2)

    result = pd.read_csv(mapping_csv)
    headers = set(result["En-tête original"].tolist())

    expected_headers = {
        "L",
        "Nature de l'inject",
        "Condition",
        "ID",
        "Statut inject",
        "Emetteur",
        "Destinataire",
        "Descriptif",
        "Corps",
        "Modalité",
        "Réactions attendues",
        "Tango",
        "N°",
        "Timing",
        "Type",
        "Saturant",
        "Nature",
        "Emmeteur",
        "Récepteur",
        "Description",
        "Actions attendues",
    }

    assert expected_headers.issubset(headers)
    assert new_added == len(expected_headers) - 1
    assert total >= len(expected_headers)
