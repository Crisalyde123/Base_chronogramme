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

    id_col = "ID_inject"
    if id_col not in data.columns or data[id_col].astype(str).str.strip().replace("nan", "").eq("").all():
        # create sequential numero_inject column
        data["numero_inject"] = list(range(1, len(data) + 1))
        logger.info("numero_inject generated", extra={"event": "AUTO_NUM"})
    else:
        mask = data[id_col].isna() | (data[id_col].astype(str).str.strip() == "")
        if mask.any():
            seq = range(1, mask.sum() + 1)
            data.loc[mask, id_col] = list(seq)
            logger.info("Missing ID_inject filled", extra={"event": "AUTO_NUM"})

    data["nb_injects"] = len(data)
    return data
