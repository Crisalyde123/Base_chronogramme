import json
import os
import sys
from pathlib import Path

# allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.logger import get_logger


def test_get_logger_creates_json_file(tmp_path, monkeypatch):
    log_dir = tmp_path / "logs"
    monkeypatch.setenv("CHRONO_LOG_DIR", str(log_dir))
    logger = get_logger("test_logger")
    logger.info("message test")
    for h in logger.handlers:
        if hasattr(h, "flush"):
            h.flush()
    files = list(log_dir.glob("run_*.log"))
    assert len(files) == 1
    content = files[0].read_text().strip()
    data = json.loads(content)
    assert data["message"] == "message test"
    assert data["level"] == "INFO"
