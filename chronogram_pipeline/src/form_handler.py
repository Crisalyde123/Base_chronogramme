"""Handle user form submission and store chronogram metadata."""

from __future__ import annotations

import re
import shutil
import unicodedata
from datetime import datetime, date
from pathlib import Path
from typing import Tuple, Dict, Any

from .logger import get_logger
from .db_utils import insert_chronogram, DEFAULT_DB, BASE_DIR

logger = get_logger(__name__)

INPUTS_DIR = BASE_DIR / "data/inputs"


def _sanitize(name: str) -> str:
    """Return a filesystem safe version of ``name``.

    Accents and special characters are removed, spaces are replaced by
    underscores and the result is lowercased.
    """
    normalized = unicodedata.normalize("NFKD", name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", ascii_name)
    cleaned = cleaned.strip("._-")
    return cleaned.lower() or "chronogramme"


def _format_date(value: str | datetime | date) -> str:
    """Return ``value`` formatted as ``YYYY-MM-DD`` if possible."""
    if isinstance(value, (datetime, date)):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                dt = datetime.strptime(value, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
    return _sanitize(str(value))


def save_excel_file(
    src: str | Path,
    etablissement_nom: str,
    nom_chronogramme: str,
    date_exercice: str | datetime | date,
    inputs_dir: Path = INPUTS_DIR,
) -> Path:
    """Copy ``src`` to ``inputs_dir`` with a structured unique file name."""

    src_path = Path(src)
    if src_path.suffix.lower() != ".xlsx":
        raise ValueError("Uploaded file must be a .xlsx Excel file")

    inputs_dir.mkdir(parents=True, exist_ok=True)

    etab = _sanitize(etablissement_nom)
    nom = _sanitize(nom_chronogramme)
    date_str = _format_date(date_exercice)

    base_name = f"Chronogramme_{etab}_{nom}_{date_str}".strip("_")
    dest_name = f"{base_name}.xlsx"
    dest_path = inputs_dir / dest_name
    if dest_path.exists():
        suffix = datetime.now().strftime("_%H%M%S")
        dest_path = inputs_dir / f"{base_name}{suffix}.xlsx"

    logger.info("Saving uploaded file to %s", dest_path)
    shutil.copy(src_path, dest_path)
    return dest_path


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

    dest_path = save_excel_file(
        form_data["file_path"],
        str(form_data.get("etablissement_nom", "")),
        str(form_data.get("nom_chronogramme", "chronogramme")),
        form_data.get("date_exercice", ""),
    )

    form_data["fichier_source"] = str(dest_path)

    chrono_id = insert_chronogram(form_data, db_path=DEFAULT_DB)
    logger.info("Inserted chronogram %s with id %s", form_data.get("nom_chronogramme"), chrono_id)

    return chrono_id, str(dest_path)

