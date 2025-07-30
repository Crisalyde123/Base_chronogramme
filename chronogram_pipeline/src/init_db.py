"""Script to initialise SQLite databases for the chronogram pipeline."""
import logging
from pathlib import Path

from db_utils import init_databases

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1] / "output/databases"
    chrono_db = base_dir / "chronogrammes.db"
    injects_db = base_dir / "injects.db"
    logger.info("Creating databases in %s", base_dir)
    init_databases(chrono_db, injects_db)


if __name__ == "__main__":
    main()
