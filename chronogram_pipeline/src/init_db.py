"""Script to initialise SQLite databases for the chronogram pipeline."""
from pathlib import Path
import os

from chronogram_pipeline.src.db_utils import init_databases
from chronogram_pipeline.src.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    """Initialise the SQLite databases used by the pipeline."""
    base_dir = Path(
        os.getenv(
            "OUTPUT_DB_PATH",
            Path(__file__).resolve().parents[1] / "output/databases",
        )
    )
    chrono_db = base_dir / "chronogrammes.db"
    injects_db = base_dir / "injects.db"
    logger.info("Creating databases in %s", base_dir)
    init_databases(chrono_db, injects_db)


if __name__ == "__main__":
    main()
