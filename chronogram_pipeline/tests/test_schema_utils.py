import sys
import importlib
import logging
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_load_schema_fields(tmp_path, monkeypatch):
    monkeypatch.setenv("CHRONO_LOG_DIR", str(tmp_path / "logs"))
    logging.getLogger("src.schema_utils").handlers.clear()
    import src.schema_utils as schema_utils
    importlib.reload(schema_utils)
    schema = tmp_path / "schema.yaml"
    schema.write_text("fields:\n  - name: A\n  - name: B\n", encoding="utf-8")
    fields = schema_utils.load_schema_fields(schema)
    assert fields == ["A", "B"]

def test_load_schema_fields_missing(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    monkeypatch.setenv("CHRONO_LOG_DIR", str(log_dir))
    logging.getLogger("src.schema_utils").handlers.clear()
    import src.schema_utils as schema_utils
    importlib.reload(schema_utils)
    missing = tmp_path / "no_schema.yaml"
    fields = schema_utils.load_schema_fields(missing)
    for h in schema_utils.logger.handlers:
        if hasattr(h, "flush"):
            h.flush()
    log_file = sorted(log_dir.glob("run_*.log"))[-1]
    content = log_file.read_text()
    assert fields == []
    assert "Schema file" in content

def test_apply_schema_columns(tmp_path, monkeypatch):
    monkeypatch.setenv("CHRONO_LOG_DIR", str(tmp_path / "logs"))
    logging.getLogger("src.schema_utils").handlers.clear()
    import src.schema_utils as schema_utils
    importlib.reload(schema_utils)
    schema = tmp_path / "schema.yaml"
    schema.write_text("""fields:\n  - name: B\n  - name: D\n  - name: A\n""", encoding="utf-8")
    df = pd.DataFrame({"A": [1], "B": [2], "C": [3]})
    out = schema_utils.apply_schema_columns(df, schema)
    assert list(out.columns) == ["B", "D", "A"]
    assert out["B"].iloc[0] == 2
    assert out["A"].iloc[0] == 1
    assert pd.isna(out["D"]).all()

def test_apply_schema_columns_missing_schema(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    monkeypatch.setenv("CHRONO_LOG_DIR", str(log_dir))
    logging.getLogger("src.schema_utils").handlers.clear()
    import src.schema_utils as schema_utils
    importlib.reload(schema_utils)
    df = pd.DataFrame({"A": [1]})
    missing = tmp_path / "missing.yaml"
    out = schema_utils.apply_schema_columns(df, missing)
    for h in schema_utils.logger.handlers:
        if hasattr(h, "flush"):
            h.flush()
    log_file = sorted(log_dir.glob("run_*.log"))[-1]
    content = log_file.read_text()
    assert out is df
    assert "Schema file" in content
