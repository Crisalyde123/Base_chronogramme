import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.standardizer import standardize_headers


def test_standardize_headers_uses_dictionary_first(tmp_path):
    mapping_csv = tmp_path / "mapping_headers.csv"
    mapping_csv.write_text("En-tête original,En-tête standard\nDescriptif,Contenu\n")

    schema_yaml = tmp_path / "schema.yaml"
    schema_yaml.write_text("fields:\n  - name: Contenu\n  - name: Destinataire\n  - name: Modalité\n")

    prompts_dir = tmp_path / "prompts"

    calls = []

    def fake_gpt(header, allowed):
        calls.append(header)
        return "Destinataire"

    headers = ["Descriptif", "Destinataires"]

    out = standardize_headers(
        headers,
        mapping_csv=mapping_csv,
        schema_path=schema_yaml,
        prompts_dir=prompts_dir,
        gpt_suggest_header=fake_gpt,
        file_name="testfile",
        log_xlsx=tmp_path / "log.xlsx",
    )

    assert out == ["Contenu", "Destinataire"]
    assert calls == ["Destinataires"]

    df = pd.read_csv(mapping_csv)
    assert "Destinataires" in df["En-tête original"].values
    # prompt saved
    assert (prompts_dir / "testfile_header_Destinataires.txt").exists()
