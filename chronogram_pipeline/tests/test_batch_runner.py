from pathlib import Path
from typing import List
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import scripts.run_all_inputs as batch


def test_process_all_invokes_pipeline(tmp_path, monkeypatch):
    calls: List[Path] = []

    def fake_run_pipeline(path: Path):
        calls.append(path)
        return {"chrono_id": 42}

    monkeypatch.setattr(batch, "run_pipeline", fake_run_pipeline)

    (tmp_path / "a.xlsx").write_text("dummy")
    (tmp_path / "b.xlsx").write_text("dummy")

    results = batch.process_all(tmp_path)

    assert calls == sorted(tmp_path.glob("*.xlsx"))
    assert results == [(tmp_path / "a.xlsx", 42), (tmp_path / "b.xlsx", 42)]


def test_main_accepts_directory(tmp_path, monkeypatch, capsys):
    (tmp_path / "a.xlsx").write_text("dummy")
    monkeypatch.setattr(
        "scripts.run_all_inputs.run_pipeline", lambda p: {"chrono_id": 1}
    )
    monkeypatch.setattr(sys, "argv", ["run_all_inputs", str(tmp_path)])

    batch.main()

    captured = capsys.readouterr().out
    assert "a.xlsx: OK (1)" in captured
