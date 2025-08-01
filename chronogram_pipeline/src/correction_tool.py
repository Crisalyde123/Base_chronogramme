# -*- coding: utf-8 -*-
"""Utility functions to manually correct mappings applied in database."""
from pathlib import Path
from typing import Dict

import pandas as pd


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
    df = pd.read_csv(csv_path, header=None)
    if df.empty or df.shape[1] < 2:
        return {}
    return dict(zip(df.iloc[:, 0].astype(str), df.iloc[:, 1].astype(str)))
