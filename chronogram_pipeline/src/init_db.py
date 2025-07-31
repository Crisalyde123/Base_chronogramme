"""Script to initialise SQLite databases for the chronogram pipeline."""
from pathlib import Path

try:
    # allow execution with `python -m chronogram_pipeline.src.init_db`
    from .db_utils import init_databases
except ImportError:  # pragma: no cover - fallback for direct execution
    import sys

    sys.path.append(str(Path(__file__).resolve().parent))
    from db_utils import init_databases  # type: ignore

from .logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    """Initialise the SQLite databases used by the pipeline."""
    base_dir = Path(__file__).resolve().parents[1] / "output/databases"
    chrono_db = base_dir / "chronogrammes.db"
    injects_db = base_dir / "injects.db"
    logger.info("Creating databases in %s", base_dir)
    init_databases(chrono_db, injects_db)


if __name__ == "__main__":
    main()
