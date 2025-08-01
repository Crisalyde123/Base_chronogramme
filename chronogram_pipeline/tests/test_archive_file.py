import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.db_utils import archive_file


def test_archive_file_moves(tmp_path):
    src = tmp_path / "sample.xlsx"
    src.write_text("dummy")
    archive_dir = tmp_path / "arc"

    dest = archive_file(src, chrono_id="C001", archive_dir=archive_dir)

    assert dest.exists()
    assert dest.parent == archive_dir
    assert not src.exists()
    assert "C001" in dest.stem
