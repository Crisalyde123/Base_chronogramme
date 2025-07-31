from __future__ import annotations

import re
import shutil
import unicodedata
from datetime import datetime, date
from pathlib import Path
from typing import Tuple, Dict, Any

import sys

# allow imports when running tests from this directory
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.logger import get_logger
from src.db_utils import insert_chronogram, DEFAULT_DB, BASE_DIR

logger = get_logger(__name__)

# Directory where uploaded files are stored
INPUTS_DIR = BASE_DIR / "data" / "inputs"


def _sanitize(name: str) -> str:
    """
    Return a filesystem-safe version of `name`:
    - strip accents & non-ASCII
    - replace non-alphanumeric chars with underscores
    - trim leading/trailing punctuation
    - lowercase (fallback to 'chronogramme' if empty)
    """
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", ascii_name)
    cleaned = cleaned.strip("._-")
    return cleaned.lower() or "chronogramme"


def _format_date(value: str | datetime | date) -> str:
    """
    If `value` is a datetime/date, return YYYY-MM-DD.
    If it’s a string, try ISO and common European formats.
    Otherwise, sanitize and return.
    """
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d")

    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue

    return _sanitize(value)


def save_excel_file(
    src: str | Path,
    etablissement_nom: str,
    nom_chronogramme: str,
    date_exercice: str | datetime | date,
    inputs_dir: Path = INPUTS_DIR,
) -> Path:
    """
    Copy `src` (.xlsx) into `inputs_dir` under a structured, unique filename:
      Chronogramme_<etablissement>_<nom>_<date>.xlsx

    Raises:
        ValueError: if src is not an .xlsx.
    """
    src_path = Path(src)
    if src_path.suffix.lower() != ".xlsx":
        raise ValueError("Uploaded file must be a .xlsx Excel file")

    inputs_dir.mkdir(parents=True, exist_ok=True)

    etab = _sanitize(etablissement_nom)
    nom = _sanitize(nom_chronogramme)
    date_str = _format_date(date_exercice)

    base_name = f"Chronogramme_{etab}_{nom}_{date_str}".strip("_")
    dest_path = inputs_dir / f"{base_name}.xlsx"

    if dest_path.exists():
        # append timestamp to avoid overwrite
        suffix = datetime.now().strftime("_%H%M%S")
        dest_path = inputs_dir / f"{base_name}{suffix}.xlsx"

    logger.info("Saving uploaded file to %s", dest_path)
    shutil.copy(src_path, dest_path)
    return dest_path


def handle_form_submission(form_data: Dict[str, Any]) -> Tuple[int, str]:
    """
    1. Rename & move uploaded Excel via save_excel_file()
    2. Insert its metadata into the DEFAULT_DB SQLite

    Expects in form_data:
      - file_path         : path to the temporary .xlsx
      - etablissement_nom : establishment name (str)
      - nom_chronogramme  : chronogram name (str)
      - date_exercice     : date (str|date|datetime)

    Returns:
      (id_chronogramme, final_file_path)
    """
    # 1) Copy & rename file
    dest_path = save_excel_file(
        src=form_data["file_path"],
        etablissement_nom=str(form_data.get("etablissement_nom", "")),
        nom_chronogramme=str(form_data.get("nom_chronogramme", "chronogramme")),
        date_exercice=form_data.get("date_exercice", ""),
    )
    form_data["fichier_source"] = str(dest_path)

    # 2) Insert metadata and get the new ID
    chrono_id = insert_chronogram(form_data, db_path=DEFAULT_DB)
    logger.info(
        "Chronogramme '%s' inserted with ID %s (file: %s)",
        form_data.get("nom_chronogramme"),
        chrono_id,
        dest_path,
    )

    return chrono_id, str(dest_path)
