from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable

import pandas as pd

from .mapping_utils import normalize_text


def _norm(value: str) -> str:
    """Return normalized key: lowercase, accentless without spaces."""
    return normalize_text(value).replace(" ", "")


def load_column_mapping(path_ref: Path) -> Dict[str, str]:
    """Return column name mapping from CSV file at ``path_ref``."""
    if not path_ref.exists():
        pd.DataFrame(
            columns=["raw_name", "mapped_name", "nom_chronogramme"]
        ).to_csv(path_ref, index=False)
        return {}

    df = pd.read_csv(path_ref, dtype=str)
    if "nom_chronogramme" not in df.columns:
        df["nom_chronogramme"] = ""

    df["norm"] = df["raw_name"].astype(str).map(_norm)
    df.sort_values(by=["norm"], inplace=True)
    df.drop_duplicates(subset=["norm"], keep="first", inplace=True)
    df.drop(columns=["norm"], inplace=True)
    df.to_csv(path_ref, index=False)

    mapping: Dict[str, str] = {}
    for _, row in df.iterrows():
        raw = str(row.get("raw_name", ""))
        mapped = "" if pd.isna(row.get("mapped_name")) else str(row.get("mapped_name"))
        if mapped == "XXX":
            continue
        key = _norm(raw)
        mapping[key] = "__DROP__" if mapped == "" else mapped

    return mapping


def load_value_mapping(path_ref: Path) -> Dict[str, Dict[str, str]]:
    """Return per-column value mapping from CSV file at ``path_ref``."""
    if not path_ref.exists():
        pd.DataFrame(
            columns=["column_name", "raw_value", "mapped_value", "nom_chronogramme"]
        ).to_csv(path_ref, index=False)
        return {}

    df = pd.read_csv(path_ref, dtype=str)
    if "nom_chronogramme" not in df.columns:
        df["nom_chronogramme"] = ""

    df["norm_col"] = df["column_name"].astype(str).map(_norm)
    df["norm_val"] = df["raw_value"].astype(str).map(_norm)
    df.sort_values(by=["norm_col", "norm_val"], inplace=True)
    df.drop_duplicates(subset=["norm_col", "norm_val"], keep="first", inplace=True)
    df.drop(columns=["norm_col", "norm_val"], inplace=True)
    df.to_csv(path_ref, index=False)

    mapping: Dict[str, Dict[str, str]] = {}
    for _, row in df.iterrows():
        col = str(row.get("column_name", ""))
        raw = str(row.get("raw_value", ""))
        mapped = "" if pd.isna(row.get("mapped_value")) else str(row.get("mapped_value"))
        if mapped == "XXX":
            continue
        mapping.setdefault(_norm(col), {})[_norm(raw)] = mapped

    return mapping


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


def _append_new_columns(path_ref: Path, columns: Iterable[str], chrono_name: str | None = None) -> None:
    """Append unknown column names to ``path_ref`` CSV with empty mapping."""
    if path_ref.exists():
        df = pd.read_csv(path_ref, dtype=str)
    else:
        df = pd.DataFrame(columns=["raw_name", "mapped_name", "nom_chronogramme"])

    if "nom_chronogramme" not in df.columns:
        df["nom_chronogramme"] = ""

    existing = set(df.get("raw_name", []).astype(str).map(_norm))
    for col in columns:
        norm = _norm(col)
        if norm not in existing:
            df.loc[len(df)] = {
                "raw_name": col,
                "mapped_name": "XXX",
                "nom_chronogramme": chrono_name or "",
            }
            existing.add(norm)

    df["norm"] = df["raw_name"].astype(str).map(_norm)
    df.sort_values(by=["norm"], inplace=True)
    df.drop_duplicates(subset=["norm"], keep="first", inplace=True)
    df.drop(columns=["norm"], inplace=True)
    df.to_csv(path_ref, index=False)


def _append_new_values(
    path_ref: Path, rows: Iterable[tuple[str, str]], chrono_name: str | None = None
) -> None:
    """Append unknown values to ``path_ref`` CSV with placeholder."""
    if path_ref.exists():
        df = pd.read_csv(path_ref, dtype=str)
    else:
        df = pd.DataFrame(columns=["column_name", "raw_value", "mapped_value", "nom_chronogramme"])

    if "nom_chronogramme" not in df.columns:
        df["nom_chronogramme"] = ""

    existing = set(
        zip(
            df.get("column_name", []).astype(str).map(_norm),
            df.get("raw_value", []).astype(str).map(_norm),
        )
    )
    for col, val in rows:
        key = (_norm(col), _norm(val))
        if key not in existing:
            df.loc[len(df)] = {
                "column_name": col,
                "raw_value": val,
                "mapped_value": "XXX",
                "nom_chronogramme": chrono_name or "",
            }
            existing.add(key)

    df["norm_col"] = df["column_name"].astype(str).map(_norm)
    df["norm_val"] = df["raw_value"].astype(str).map(_norm)
    df.sort_values(by=["norm_col", "norm_val"], inplace=True)
    df.drop_duplicates(subset=["norm_col", "norm_val"], keep="first", inplace=True)
    df.drop(columns=["norm_col", "norm_val"], inplace=True)
    df.to_csv(path_ref, index=False)


def _apply_mappings(
    df: pd.DataFrame,
    column_map: Dict[str, str],
    value_map: Dict[str, Dict[str, str]],
    *,
    columns_file: Path,
    values_file: Path,
    chrono_name: str | None = None,
) -> pd.DataFrame:
    """Rename columns and replace values using provided mappings."""
    df = df.copy()

    unknown_cols = [c for c in df.columns if _norm(c) not in column_map]
    if unknown_cols:
        _append_new_columns(columns_file, unknown_cols, chrono_name)
        raise StopIteration("Nouveau nom de colonne à mapper")

    rename: Dict[str, str] = {}
    drop_cols = []
    for col in df.columns:
        mapped = column_map.get(_norm(col))
        if mapped == "__DROP__":
            drop_cols.append(col)
        else:
            rename[col] = mapped

    df = df.rename(columns=rename)
    if drop_cols:
        df.drop(columns=drop_cols, inplace=True)

    for col in list(df.columns):
        mapping = value_map.get(_norm(col))
        if not mapping:
            continue
        new_vals: list[str] = []

        def convert(val):
            if pd.isna(val) or str(val).strip() == "":
                return pd.NA
            raw = str(val)
            norm_val = _norm(raw)
            if norm_val not in mapping:
                new_vals.append(raw)
                return pd.NA
            mapped_val = mapping[norm_val]
            return pd.NA if mapped_val == "" else mapped_val

        df[col] = df[col].map(convert)

        if new_vals:
            _append_new_values(values_file, [(col, v) for v in new_vals], chrono_name)
            raise StopIteration("Nouvelles valeurs à mapper")

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
            if c in row.index and pd.notna(row[c]) and str(row[c]).strip() != ""
        ]
        if not values:
            return False
        counts: Dict[str, int] = {}
        for v in values:
            counts[v] = counts.get(v, 0) + 1
        return max(counts.values()) >= 6

    mask = df.apply(is_repeat, axis=1)
    cleaned = df.loc[~mask].reset_index(drop=True)
    if cleaned.empty and not df.empty:
        return df.reset_index(drop=True)
    return cleaned


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

    rename: Dict[str, str] = {}
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


def clean_data(
    df: pd.DataFrame,
    *,
    chrono_rank: int = 1,
    column_map: Dict[str, str] | None = None,
    value_map: Dict[str, Dict[str, str]] | None = None,
    columns_file: Path | None = None,
    values_file: Path | None = None,
    chrono_name: str | None = None,
) -> pd.DataFrame:
    """Return ``df`` cleaned, optionally using manual mappings."""
    df = unmerge_cells(df)
    df = drop_empty_rows(df)
    df = drop_empty_cols(df)
    df = remove_parasitic_rows(df)
    df.reset_index(drop=True, inplace=True)

    if column_map is not None and columns_file is not None and values_file is not None:
        df = _apply_mappings(
            df,
            column_map,
            value_map or {},
            columns_file=columns_file,
            values_file=values_file,
            chrono_name=chrono_name,
        )

    df = standardize_and_clean(df, chrono_rank=chrono_rank)
    return df
