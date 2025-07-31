import importlib
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_default_log_path(tmp_path, monkeypatch):
    control_dir = tmp_path / "ctrl"
    monkeypatch.setenv("CHRONO_LOG_DIR", str(control_dir))

    import src.standardizer as standardizer
    importlib.reload(standardizer)

    mapping_csv = tmp_path / "map.csv"
    mapping_csv.write_text("En-tete original,En-tete standard\nA,B\n")

    standardizer.standardize_headers_rules(["A"], mapping_csv=mapping_csv)

    log_file = control_dir / "mappings_log.xlsx"
    assert log_file.exists()
    df = pd.read_excel(log_file)
    assert df.shape[0] == 1
