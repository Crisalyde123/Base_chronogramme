"""Data cleaning utilities for chronogram tables."""

from __future__ import annotations

from datetime import datetime
import pandas as pd

from .mapping_utils import normalize_text


def unmerge_cells(df: pd.DataFrame) -> pd.DataFrame:
    """Propagate merged cell values vertically and horizontally."""
    result = df.copy()

    # Forward-fill downwards first to handle vertical merges
    result = result.ffill()

    # ``result`` might be a Series if ``df`` was not a DataFrame.  ``Series``
    # does not support ``ffill`` with ``axis`` so convert it to a single-row
    # DataFrame before applying the horizontal fill.
    if isinstance(result, pd.Series):
        result = result.to_frame().T

    # Propagate values horizontally (left -> right)
    result = result.ffill(axis=1)
    return result


def drop_empty_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Remove rows that are completely empty or contain only blanks."""
    df = df.copy()
    df.replace(r"^\s*$", pd.NA, regex=True, inplace=True)
    df.dropna(axis=0, how="all", inplace=True)
    return df


def drop_empty_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Remove columns that contain no data below the header row."""
    df = df.copy()
    df.replace(r"^\s*$", pd.NA, regex=True, inplace=True)
    data = df.iloc[1:] if len(df) > 1 else df
    empty = [col for col in df.columns if data[col].isna().all()]
    df.drop(columns=empty, inplace=True)
    return df


def remove_parasitic_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows like 'TOTAL' or 'Phase X' that do not contain data."""
    df = df.copy()
    keywords = ("total", "phase")

    def is_parasitic(row) -> bool:
        """Return ``True`` if ``row`` looks like a summary row."""
        cells = [
            str(c).strip().lower()
            for c in row
            if not pd.isna(c) and str(c).strip() != ""
        ]
        if len(cells) == 1:
            val = cells[0]
            return any(val.startswith(k) for k in keywords)
        return False

    mask = df.apply(is_parasitic, axis=1)
    df = df[~mask]
    return df


def _validate_values(df: pd.DataFrame) -> None:
    """Normalize and validate values for specific columns."""

    allowed = {
        "phase": {"1": "1", "2": "2", "3": "3", "4": "4"},
        "statut": {"joue": "joué", "annule": "annulé", "a jouer": "à jouer"},
        "type": {"structurant": "structurant", "saturant": "saturant"},
        "nature": {
            "mail": "mail",
            "appel": "appel",
            "sms": "SMS",
            "video": "vidéo",
            "weezer": "Weezer",
            "oral": "oral",
        },
    }

    for col, mapping in allowed.items():
        if col not in df.columns:
            continue

        def convert(val):
            if pd.isna(val) or str(val).strip() == "":
                return pd.NA
            key = normalize_text(val)
            return mapping.get(key, pd.NA)

        df[col] = df[col].map(convert)

    if "horodatage" in df.columns:
        def parse_ts(val):
            if pd.isna(val) or str(val).strip() == "":
                return pd.NA
            ts = pd.to_datetime(str(val), dayfirst=True, errors="coerce")
            if pd.isna(ts):
                return pd.NA
            return ts.strftime("%Y-%m-%dT%H:%M:%S")

        df["horodatage"] = df["horodatage"].map(parse_ts)


def _drop_repeated_rows(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Remove rows where the same value appears in >=6 columns."""

    def is_repeat(row: pd.Series) -> bool:
        values = [
            str(row[c]).strip()
            for c in cols
            if c in row and not pd.isna(row[c]) and str(row[c]).strip() != ""
        ]
        if not values:
            return False
        counts = {}
        for v in values:
            counts[v] = counts.get(v, 0) + 1
        return max(counts.values()) >= 6

    mask = df.apply(is_repeat, axis=1)
    return df.loc[~mask].reset_index(drop=True)


def standardize_and_clean(df: pd.DataFrame, *, chrono_rank: int = 1) -> pd.DataFrame:
    """Standardize columns and add identifier columns."""

    mapping = {
        "phase": "phase",
        "statut inject": "statut",
        "statut": "statut",
        "type": "type",
        "horodatage": "horodatage",
        "emetteur": "emetteur",
        "emmeteur": "emetteur",
        "destinataire": "recepteur",
        "recepteur": "recepteur",
        "nature": "nature",
        "descriptif": "resume",
        "description": "resume",
        "resume": "resume",
        "corps": "contenu",
        "contenu": "contenu",
        "actions attendues": "actions_attendues",
        "reactions attendues": "actions_attendues",
        "commentaires": "commentaires",
        "observations": "commentaires",
    }

    std_cols = [
        "phase",
        "statut",
        "type",
        "horodatage",
        "emetteur",
        "recepteur",
        "nature",
        "resume",
        "contenu",
        "actions_attendues",
        "commentaires",
    ]

    rename = {}
    for col in list(df.columns):
        norm = normalize_text(col)
        if norm in mapping:
            rename[col] = mapping[norm]

    data = df.rename(columns=rename)
    for col in std_cols:
        if col not in data.columns:
            data[col] = pd.NA

    data = _drop_repeated_rows(data, std_cols)
    _validate_values(data)

    chrono_id = f"C{chrono_rank:03d}"
    numeros = [f"L{i:03d}" for i in range(1, len(data) + 1)]
    data.insert(0, "id_chronogramme", chrono_id)
    data.insert(1, "numero", numeros)
    data.insert(2, "id_inject", [f"{chrono_id}_{n}" for n in numeros])
    data.replace({pd.NA: None}, inplace=True)

    return data


def clean_data(df: pd.DataFrame, *, chrono_rank: int = 1) -> pd.DataFrame:
    """Return ``df`` cleaned and standardized."""
    df = unmerge_cells(df)
    df = drop_empty_rows(df)
    df = drop_empty_cols(df)
    df = remove_parasitic_rows(df)
    df.reset_index(drop=True, inplace=True)
    df = standardize_and_clean(df, chrono_rank=chrono_rank)
    return df
