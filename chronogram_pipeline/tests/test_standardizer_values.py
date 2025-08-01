import sys
from pathlib import Path
import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.standardizer import standardize_column_values


def test_standardize_column_values(tmp_path):
    df = pd.DataFrame(
        {
            "type_inject": ["Majeur", "Critique", "Élevé"],
            "modalite": ["SMS", "Courriel", "SMS"],
        }
    )

    value_yaml = tmp_path / "value_mappings.yaml"
    value_yaml.write_text(
        """
type_inject:
  majeur: Critique
modalite:
  courriel: Email
""",
        encoding="utf-8",
    )

    schema = tmp_path / "schema.yaml"
    schema.write_text(
        """
fields:
  - name: type_inject
    values: [Critique, Important, Secondaire]
  - name: modalite
    values: [Email, SMS]
""",
        encoding="utf-8",
    )

    prompts_dir = tmp_path / "prompts"
    calls = []

    def fake_gpt(value, allowed):
        calls.append(value)
        return "Important"

    log_file = tmp_path / "log.xlsx"

    out = standardize_column_values(
        df.copy(),
        mapping_yaml=value_yaml,
        schema_path=schema,
        prompts_dir=prompts_dir,
        gpt_suggest_value=fake_gpt,
        file_name="testfile",
        log_xlsx=log_file,
        id_chronogramme="C005",
    )

    assert list(out["type_inject"]) == ["Critique", "Critique", "Important"]
    assert list(out["modalite"]) == ["SMS", "Email", "SMS"]
    assert calls == ["Élevé"]
    assert (prompts_dir / "testfile_type_inject_Élevé.txt").exists()

    data = yaml.safe_load(value_yaml.read_text())
    assert data["type_inject"]["majeur"] == "Critique"
    assert data["type_inject"]["eleve"] == "Important"

    log_df = pd.read_excel(log_file)
    assert set(log_df["id_chronogramme"]) == {"C005"}
