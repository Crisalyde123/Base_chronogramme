import sys
import shutil
from pathlib import Path
import pandas as pd

# allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.mapping_utils import enrich_mapping_values, update_mapping_headers

def test_enrich_mapping_values(tmp_path):
    # Prepare temporary mapping files
    header_map = tmp_path / "mapping_headers.csv"
    header_map.write_text("En-tete original,En-tete standard\n")

    values_csv = tmp_path / "mapping_values.csv"
    values_csv.write_text("Colonne,Valeur brute,Valeur standard\n")

    # Create sample Excel file
    df = pd.DataFrame({
        "Emetteur": ["A", "B"],
        "Destinataire": ["X", "Y"],
        "Type d'inject": ["Maj", "Min"],
        "Modalite": ["SMS", "Mail"],
    })
    excel_file = tmp_path / "sample.xlsx"
    df.to_excel(excel_file, index=False)

    # Run enrichment
    enrich_mapping_values(tmp_path, header_map, values_csv, limit=1)

    result = pd.read_csv(values_csv)
    # Expect 8 rows (4 columns x 2 unique values)
    assert len(result) == 8
    assert (result["Colonne"] == "emetteur").sum() == 2
    assert (result["Colonne"] == "destinataire").sum() == 2
    assert (result["Colonne"] == "type_inject").sum() == 2
    assert (result["Colonne"] == "modalite").sum() == 2

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
