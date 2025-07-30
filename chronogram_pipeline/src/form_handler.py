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


def handle_form_submission(form_data: Dict[str, Any]) -> Tuple[int, str]:
    """Save uploaded Excel file and insert metadata.

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
    INPUTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    base = _sanitize(str(form_data.get("nom_chronogramme", "chronogramme")))
    dest_name = f"{base}_{timestamp}{src_path.suffix}"
    dest_path = INPUTS_DIR / dest_name

    logger.info("Saving uploaded file to %s", dest_path)
    shutil.move(str(src_path), dest_path)

    form_data["fichier_source"] = str(dest_path)

    chrono_id = insert_chronogram(form_data, db_path=DEFAULT_DB)
    logger.info("Inserted chronogram %s with id %s", form_data.get("nom_chronogramme"), chrono_id)

    return chrono_id, str(dest_path)

