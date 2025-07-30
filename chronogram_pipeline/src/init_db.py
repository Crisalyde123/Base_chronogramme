"""Script to initialise SQLite databases for the chronogram pipeline."""
from pathlib import Path

from db_utils import init_databases
from .logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1] / "output/databases"
    chrono_db = base_dir / "chronogrammes.db"
    injects_db = base_dir / "injects.db"
    logger.info("Creating databases in %s", base_dir)
    init_databases(chrono_db, injects_db)


if __name__ == "__main__":
    main()
