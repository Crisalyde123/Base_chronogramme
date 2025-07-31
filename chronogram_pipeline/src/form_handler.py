from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Tuple, Dict, Any

from .logger import get_logger
from .db_utils import insert_chronogram, DEFAULT_DB
from .form_handler_utils import save_excel_file  # importer votre utilitaire

logger = get_logger(__name__)


def handle_form_submission(form_data: Dict[str, Any]) -> Tuple[int, str]:
    """Traite la soumission du formulaire : copie le fichier Excel, insère les métadata
    et renvoie l'ID du chronogramme ainsi que le chemin final du fichier.

    Attendu dans form_data :
      - "file_path"           : chemin vers le fichier temporaire (.xlsx)
      - "etablissement_nom"   : nom de l'établissement
      - "nom_chronogramme"    : nom du chronogramme
      - "date_exercice"       : date (str|date|datetime)

    Retourne :
      - (id_chronogramme, chemin_final_du_fichier)
    """
    # 1. Déplacement + renommage du fichier
    dest_path = save_excel_file(
        src=form_data["file_path"],
        etablissement_nom=str(form_data.get("etablissement_nom", "")),
        nom_chronogramme=str(form_data.get("nom_chronogramme", "chronogramme")),
        date_exercice=form_data.get("date_exercice", "")
    )
    form_data["fichier_source"] = str(dest_path)

    # 2. Insertion des métadonnées en base
    chrono_id = insert_chronogram(form_data, db_path=DEFAULT_DB)
    logger.info(
        "Chronogramme '%s' inséré avec l'ID %s (fichier : %s)",
        form_data.get("nom_chronogramme"),
        chrono_id,
        dest_path
    )

    return chrono_id, str(dest_path)
