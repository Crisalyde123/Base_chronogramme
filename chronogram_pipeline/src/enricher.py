from __future__ import annotations

import pandas as pd

from .logger import get_logger

logger = get_logger(__name__)


def enrich_data(
    df: pd.DataFrame,
    *,
    id_chronogramme: int,
    etablissement_nom: str,
    etablissement_type: str,
    nom_chronogramme: str,
    date_exercice: str,
) -> pd.DataFrame:
    """Add contextual metadata columns and inject numbering.

    Parameters
    ----------
    df : DataFrame
        Clean and standardised table of injects.
    id_chronogramme : int
        Identifier of the parent chronogram.
    etablissement_nom : str
        Establishment name.
    etablissement_type : str
        Establishment type.
    nom_chronogramme : str
        Chronogram name.
    date_exercice : str
        Exercise date.

    Returns
    -------
    DataFrame
        The enriched DataFrame ready for database insertion.
    """
    data = df.copy()

    # add context columns
    data["id_chronogramme"] = id_chronogramme
    data["etablissement_nom"] = etablissement_nom
    data["etablissement_type"] = etablissement_type
    data["nom_chronogramme"] = nom_chronogramme
    data["date_exercice"] = date_exercice

    # sequential numbering and unique inject identifier
    data["numero"] = list(range(1, len(data) + 1))
    data["id_inject"] = [f"C{id_chronogramme:03d}_L{num:03d}" for num in data["numero"]]
    logger.info("numero generated", extra={"event": "AUTO_NUM"})

    data["nb_injects"] = len(data)
    return data
