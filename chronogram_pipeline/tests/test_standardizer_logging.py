import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def test_standardize_headers_logs_ai_call(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    monkeypatch.setenv("CHRONO_LOG_DIR", str(log_dir))

    import importlib
    import src.standardizer as standardizer
    from src.logger import get_logger
    importlib.reload(standardizer)
    standardizer.logger = get_logger("std_test")
    standardize_headers = standardizer.standardize_headers

    mapping_csv = tmp_path / "mapping.csv"
    mapping_csv.write_text("")

    schema = tmp_path / "schema.yaml"
    schema.write_text("fields:\n  - name: Destinataire\n")

    prompts = tmp_path / "prompts"

    def fake(header, allowed):
        return "Destinataire"

    standardize_headers(
        ["Dest"],
        mapping_csv=mapping_csv,
        schema_path=schema,
        prompts_dir=prompts,
        gpt_suggest_header=fake,
        file_name="sample",
        log_xlsx=tmp_path / "log.xlsx",
    )

    log_file = sorted(log_dir.glob("run_*.log"))[-1]
    entries = [json.loads(l) for l in log_file.read_text().splitlines()]
    assert any(e.get("event") == "IA_CALL" and e.get("type") == "header" for e in entries)
