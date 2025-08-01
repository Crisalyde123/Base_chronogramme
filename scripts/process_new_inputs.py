from __future__ import annotations

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from chronogram_pipeline.src.logger import get_logger
from chronogram_pipeline.src.db_utils import archive_file, BASE_DIR as DATA_BASE_DIR
from main import run_pipeline


def process_new(inputs_dir: Path | None = None) -> list[tuple[Path, int | None]]:
    """Process and archive every Excel file found in *inputs_dir*."""
    if inputs_dir is None:
        inputs_dir = DATA_BASE_DIR / "data" / "inputs"

    logger = get_logger("new_files")
    files = sorted(p for p in inputs_dir.glob("*.xlsx") if p.is_file())
    results: list[tuple[Path, int | None]] = []
    for xlsx in files:
        try:
            logger.info("Processing %s", xlsx.name)
            res = run_pipeline(xlsx)
            cid = res.get("chrono_id")
            archive_file(xlsx, chrono_id=cid)
            logger.info("SUCCESS %s -> %s", xlsx.name, cid)
        except Exception as exc:  # pragma: no cover - just log failure
            logger.exception("FAILED %s", xlsx, exc_info=exc)
            cid = None
        results.append((xlsx, cid))
    return results


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Process new Excel files")
    parser.add_argument(
        "inputs_dir",
        nargs="?",
        type=Path,
        help="Directory containing input .xlsx files (defaults to data/inputs)",
    )
    args = parser.parse_args()

    results = process_new(args.inputs_dir)
    for file, chrono_id in results:
        status = "OK" if chrono_id is not None else "ERROR"
        cid = chrono_id if chrono_id is not None else "-"
        print(f"{file.name}: {status} ({cid})")


if __name__ == "__main__":
    main()
