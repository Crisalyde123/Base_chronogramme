"""Handle user form submission and store chronogram metadata."""

from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Tuple, Dict, Any

from .logger import get_logger
from .db_utils import insert_chronogram, DEFAULT_DB, BASE_DIR

logger = get_logger(__name__)

INPUTS_DIR = BASE_DIR / "data/inputs"


def _sanitize(name: str) -> str:
    """Return a filesystem safe version of ``name``."""
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._-")
    return cleaned or "chronogramme"


def _format_component(value: str) -> str:
    """Return cleaned and title-cased component for filename."""
    cleaned = _sanitize(value)
    parts = [p for p in cleaned.split("_") if p]
    formatted = "_".join(part if part.isupper() else part.capitalize() for part in parts)
    return formatted


def handle_form_submission(form_data: Dict[str, Any]) -> Tuple[int, str]:
    """Save uploaded Excel file and insert metadata.

    The uploaded Excel file is renamed using ``etablissement_nom``,
    ``nom_chronogramme`` and ``date_exercice`` fields in the form. Each
    component is sanitized and capitalized, then combined as
    ``Chronogramme_<etablissement>_<nom>_<date>.xlsx``. If a file with the same
    name already exists, a timestamp suffix is appended to ensure uniqueness.

    Parameters
    ----------
    form_data : dict
        Dictionary containing form fields and ``file_path`` key pointing to the
        temporary uploaded Excel file.

    Returns
    -------
    tuple
        ``(id_chronogramme, final_path)`` where ``final_path`` is the path of
        the stored Excel file.
    """

    src_path = Path(form_data["file_path"])
    if src_path.suffix.lower() != ".xlsx":
        raise ValueError("File must be .xlsx")

    INPUTS_DIR.mkdir(parents=True, exist_ok=True)

    etab = _format_component(str(form_data.get("etablissement_nom", "")))
    name = _format_component(str(form_data.get("nom_chronogramme", "")))
    date = _format_component(str(form_data.get("date_exercice", "")))
    base_parts = [part for part in [etab, name, date] if part]
    base_name = "Chronogramme_" + "_".join(base_parts)
    dest_path = INPUTS_DIR / f"{base_name}.xlsx"

    if dest_path.exists():
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        dest_path = INPUTS_DIR / f"{base_name}_{timestamp}.xlsx"

    logger.info("Saving uploaded file to %s", dest_path)
    shutil.move(str(src_path), dest_path)

    form_data["fichier_source"] = str(dest_path)

    chrono_id = insert_chronogram(form_data, db_path=DEFAULT_DB)
    logger.info("Inserted chronogram %s with id %s", form_data.get("nom_chronogramme"), chrono_id)

    return chrono_id, str(dest_path)

