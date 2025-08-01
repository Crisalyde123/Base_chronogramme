import sys
from pathlib import Path
import yaml
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.standardizer import (
    _load_mapping_normalized,
    _load_value_mappings,
    _load_allowed_values,
)


def test_load_mapping_normalized(tmp_path):
    csv_path = tmp_path / "map.csv"
    csv_path.write_text(
        "En-tete original,En-tete standard\nÀ Faire,Action\nstatut,Statut\n",
        encoding="utf-8",
    )
    mapping = _load_mapping_normalized(csv_path)
    assert mapping["a faire"] == "Action"
    assert mapping["statut"] == "Statut"


def test_load_value_mappings(tmp_path):
    yaml_path = tmp_path / "vals.yaml"
    yaml_data = {"statut": {"joué": "OK", "annulé": "KO"}}
    yaml_path.write_text(yaml.safe_dump(yaml_data, allow_unicode=True), encoding="utf-8")
    mapping = _load_value_mappings(yaml_path)
    assert mapping["statut"]["joue"] == "OK"
    assert mapping["statut"]["annule"] == "KO"


def test_load_allowed_values(tmp_path):
    schema = tmp_path / "schema.yaml"
    schema.write_text(
        """
fields:
  - name: phase
    values: [1, 2]
  - name: statut
    values: [A, B]
""",
        encoding="utf-8",
    )
    allowed = _load_allowed_values(schema)
    assert allowed == {"phase": ["1", "2"], "statut": ["A", "B"]}

