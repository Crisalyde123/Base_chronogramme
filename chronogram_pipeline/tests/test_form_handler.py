from __future__ import annotations

import shutil
from pathlib import Path
from typing import Tuple, Dict, Any

from .logger import get_logger
from .db_utils import insert_chronogram, DEFAULT_DB
from .form_handler_utils import save_excel_file  # ou là où vous avez placé cette fonction

logger = get_logger(__name__)


def handle_form_submission(form_data: Dict[str, Any]) -> Tuple[int, str]:
    """Traite la soumission du formulaire : déplace le fichier Excel dans INPUTS_DIR
    en lui donnant un nom structuré, puis insère les métadonnées en base.

    form_data doit contenir :
      - "file_path"          : chemin vers le .xlsx temporaire
      - "etablissement_nom"  : nom de l’établissement
      - "nom_chronogramme"   : nom du chronogramme
      - "date_exercice"      : date (str|date|datetime)

    Retourne (id_chronogramme, chemin_final_du_fichier).
    """
    # 1) on délègue tout le renommage / déplacement à save_excel_file
    dest_path = save_excel_file(
        src=form_data["file_path"],
        etablissement_nom=str(form_data.get("etablissement_nom", "")),
        nom_chronogramme=str(form_data.get("nom_chronogramme", "chronogramme")),
        date_exercice=form_data.get("date_exercice", ""),
    )
    form_data["fichier_source"] = str(dest_path)

    # 2) on insère en base
    chrono_id = insert_chronogram(form_data, db_path=DEFAULT_DB)
    logger.info(
        "Chronogramme '%s' inséré avec l'ID %s (fichier : %s)",
        form_data.get("nom_chronogramme"),
        chrono_id,
        dest_path,
    )

    return chrono_id, str(dest_path)
