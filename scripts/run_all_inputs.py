from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Tuple

from chronogram_pipeline.src.logger import get_logger
from main import run_pipeline


def process_all(inputs_dir: Path | None = None) -> List[Tuple[Path, int | None]]:
    """Run the pipeline on every ``.xlsx`` file in *inputs_dir*.

    Parameters
    ----------
    inputs_dir: Path, optional
        Directory containing Excel files. Defaults to
        ``chronogram_pipeline/data/inputs`` next to this script.

    Returns
    -------
    list of (Path, int | None)
        Tuples with the file path and the created chronogram id
        (``None`` if processing failed).
    """
    base_dir = Path(__file__).resolve().parents[1]
    if inputs_dir is None:
        inputs_dir = base_dir / "chronogram_pipeline" / "data" / "inputs"

    files = sorted(p for p in inputs_dir.glob("*.xlsx") if p.is_file())
    logger = get_logger("batch_runner")
    results: List[Tuple[Path, int | None]] = []
    if not files:
        logger.info("No Excel files found in %s", inputs_dir)
        return results

    for xlsx in files:
        logger.info("Processing %s", xlsx.name)
        try:
            res = run_pipeline(xlsx)
            chrono_id = res.get("chrono_id")
            logger.info("SUCCESS %s -> %s", xlsx.name, chrono_id)
        except Exception as exc:  # pragma: no cover - just log failure
            chrono_id = None
            logger.exception("FAILED %s", xlsx, exc_info=exc)
        results.append((xlsx, chrono_id))
    return results


def main() -> None:
    results = process_all()
    for file, chrono_id in results:
        status = "OK" if chrono_id is not None else "ERROR"
        cid = chrono_id if chrono_id is not None else "-"
        print(f"{file.name}: {status} ({cid})")


if __name__ == "__main__":
    main()
