# -*- coding: utf-8 -*-
"""Utility functions to manually correct mappings applied in database."""
from pathlib import Path
from typing import Dict

from pandas.errors import EmptyDataError

import pandas as pd

from .logger import get_logger

logger = get_logger(__name__)


def csv_to_dict(csv_path: Path) -> Dict[str, str]:
    """Convertit le contenu d'un fichier CSV en dictionnaire.

    Parameters
    ----------
    csv_path : Path
        Chemin du fichier CSV contenant deux colonnes :
        la première pour les clés, la seconde pour les valeurs.

    Returns
    -------
    Dict[str, str]
        Dictionnaire ``{cle: valeur}`` généré à partir des colonnes du fichier.
    """
    logger.debug("Reading CSV corrections from %s", csv_path)
    try:
        df = pd.read_csv(csv_path, header=None)
    except EmptyDataError:
        logger.warning("Empty or invalid CSV file %s", csv_path)
        return {}
    if df.empty or df.shape[1] < 2:
        logger.warning("Empty or invalid CSV file %s", csv_path)
        return {}
    mapping = dict(zip(df.iloc[:, 0].astype(str), df.iloc[:, 1].astype(str)))
    logger.debug("Loaded %d correction entries", len(mapping))
    return mapping
