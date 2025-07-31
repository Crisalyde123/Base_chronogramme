import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.pipeline_logger import PipelineLogger


def test_pipeline_logger_records_steps(tmp_path, monkeypatch):
    monkeypatch.setenv("CHRONO_LOG_DIR", str(tmp_path))
    plog = PipelineLogger("test_pipeline")

    with plog.step("STEP1") as m:
        m["lines"] = 10

    plog.summary()

    log_file = list(Path(tmp_path).glob("run_*.log"))[0]
    lines = [json.loads(l) for l in log_file.read_text().splitlines()]
    events = [l["event"] for l in lines]
    assert "STEP_START" in events
    assert "STEP_END" in events
    assert lines[-1]["event"] == "SUMMARY"
    assert lines[-1]["status"] == "SUCCES"
