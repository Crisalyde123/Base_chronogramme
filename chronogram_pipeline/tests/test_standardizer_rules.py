import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.standardizer import standardize_headers_rules


def test_standardize_headers_rules(tmp_path):
    mapping_csv = tmp_path / "mapping_headers.csv"
    mapping_csv.write_text(
        "En-tete original,En-tete standard\nDescriptif,Contenu\nDestinataires,Destinataire\n"
    )

    log_xlsx = tmp_path / "log.xlsx"
    headers = ["Descriptif", "destinataires", "Inconnu"]

    out = standardize_headers_rules(headers, mapping_csv=mapping_csv, log_xlsx=log_xlsx)

    assert out == ["Contenu", "Destinataire", ""]

    df = pd.read_excel(log_xlsx)
    assert df.shape[0] == 3
    assert (df["Méthode"] == "règle").all()
