from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable

import csv
import pandas as pd

from .mapping_utils import normalize_text
from .logger import get_logger

logger = get_logger(__name__)


def _norm(value: str) -> str:
    """Return normalized key: lowercase, accentless without spaces."""
    return normalize_text(value).replace(" ", "")


def _log_history(path: Path, rows: list[Dict[str, str]]) -> None:
    """Append mapping history rows to ``path``."""
    if not rows:
        return
    if path.exists():
        df = pd.read_csv(path)
    else:
        df = pd.DataFrame(
            columns=["timestamp", "chronogramme", "category", "column", "raw", "mapped"]
        )
    for row in rows:
        df.loc[len(df)] = row
    df.to_csv(path, index=False, quoting=csv.QUOTE_MINIMAL)


def load_column_mapping(path_ref: Path, history_file: Path | None = None) -> Dict[str, str]:
    """Return column name mapping from CSV and purge applied lines.

    Entries with ``mapped_name`` equal to ``"XXX"`` are left in ``path_ref`` for
    later manual mapping. Other lines are removed from the file and optionally
    appended to ``history_file``.
    """
    if not path_ref.exists():
        pd.DataFrame(
            columns=["raw_name", "mapped_name", "nom_chronogramme"]
        ).to_csv(path_ref, index=False, quoting=csv.QUOTE_MINIMAL)
        logger.info("Created column mapping file %s", path_ref)
        return {}

    df = pd.read_csv(path_ref, dtype=str)
    if "nom_chronogramme" not in df.columns:
        df["nom_chronogramme"] = ""

    # Normalize raw names for de-duplication but keep the original value when
    # building the resulting dictionary.
    df["norm"] = df["raw_name"].astype(str).map(_norm)
    df.sort_values(by=["norm"], inplace=True)
    df.drop_duplicates(subset=["norm"], keep="first", inplace=True)

    mapping_rows = []
    remaining_rows = []
    mapping: Dict[str, str] = {}
    for _, row in df.iterrows():
        raw = str(row.get("raw_name", ""))
        mapped = "" if pd.isna(row.get("mapped_name")) else str(row.get("mapped_name"))
        if mapped == "XXX":
            remaining_rows.append(row)
            continue
        if mapped == "":
            mapping_rows.append(
                {
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "chronogramme": row.get("nom_chronogramme", ""),
                    "category": "header",
                    "column": raw,
                    "raw": raw,
                    "mapped": mapped,
                }
            )
            mapping[raw] = "__DROP__"
            continue
        if len(mapped) == 1 and mapped.isupper():
            remaining_rows.append(row)
            continue
        mapping_rows.append(
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "chronogramme": row.get("nom_chronogramme", ""),
                "category": "header",
                "column": raw,
                "raw": raw,
                "mapped": mapped,
            }
        )
        mapping[raw] = "__DROP__" if mapped == "" else mapped

    if history_file is not None:
        _log_history(history_file, mapping_rows)

    new_df = pd.DataFrame(remaining_rows, columns=df.columns)
    if "norm" in new_df.columns:
        new_df.drop(columns=["norm"], inplace=True)
    new_df.to_csv(path_ref, index=False, quoting=csv.QUOTE_MINIMAL)

    logger.debug("Loaded %d column mappings from %s", len(mapping), path_ref)
    return mapping


def load_value_mapping(path_ref: Path, history_file: Path | None = None) -> Dict[str, Dict[str, str]]:
    """Return value mapping from CSV and purge applied lines.

    Rows with ``mapped_value`` equal to ``"XXX"`` stay in ``path_ref`` for later
    manual completion. Other rows are removed and optionally appended to
    ``history_file``.
    """
    if not path_ref.exists():
        pd.DataFrame(
            columns=["column_name", "raw_value", "mapped_value", "nom_chronogramme"]
        ).to_csv(path_ref, index=False, quoting=csv.QUOTE_MINIMAL)
        logger.info("Created value mapping file %s", path_ref)
        return {}

    df = pd.read_csv(path_ref, dtype=str)
    if "nom_chronogramme" not in df.columns:
        df["nom_chronogramme"] = ""

    # Normalize columns/values for de-duplication
    df["norm_col"] = df["column_name"].astype(str).map(_norm)
    df["norm_val"] = df["raw_value"].astype(str).map(_norm)
    df.sort_values(by=["norm_col", "norm_val"], inplace=True)
    df.drop_duplicates(subset=["norm_col", "norm_val"], keep="first", inplace=True)

    mapping_rows = []
    remaining_rows = []
    mapping: Dict[str, Dict[str, str]] = {}
    allowed = {
        "phase": {"1", "2", "3", "4"},
        "statut": {"joue", "annule", "a jouer"},
        "type": {"structurant", "saturant"},
        "nature": {"mail", "appel", "sms", "video", "weezer", "oral"},
    }
    for _, row in df.iterrows():
        col = str(row.get("column_name", ""))
        raw = str(row.get("raw_value", ""))
        mapped = "" if pd.isna(row.get("mapped_value")) else str(row.get("mapped_value"))
        if mapped == "XXX":
            remaining_rows.append(row)
            continue
        col_norm = _norm(col)
        allowed_vals = allowed.get(col_norm)
        if allowed_vals is not None and (_norm(mapped) not in allowed_vals and mapped != "__EMPTY__"):
            remaining_rows.append(row)
            continue
        mapping_rows.append(
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "chronogramme": row.get("nom_chronogramme", ""),
                "category": col,
                "column": col,
                "raw": raw,
                "mapped": mapped,
            }
        )
        mapping.setdefault(col, {})[raw] = "" if mapped == "__EMPTY__" else mapped

    if history_file is not None:
        _log_history(history_file, mapping_rows)

    new_df = pd.DataFrame(remaining_rows, columns=df.columns)
    if {"norm_col", "norm_val"}.issubset(new_df.columns):
        new_df.drop(columns=["norm_col", "norm_val"], inplace=True)
    new_df.to_csv(path_ref, index=False, quoting=csv.QUOTE_MINIMAL)

    logger.debug("Loaded value mapping for %d columns from %s", len(mapping), path_ref)
    return mapping


def unmerge_cells(df: pd.DataFrame) -> pd.DataFrame:
    """Propagate merged cell values vertically and horizontally."""
    result = df.copy()

    # Forward-fill downwards first to handle vertical merges
    result = result.ffill()

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


def _append_new_columns(path_ref: Path, arg1: Iterable[str] | str, arg2: Iterable[str] | str | None = None) -> None:
    """Append unknown column names to ``path_ref`` CSV with empty mapping.

    The historical call signature placed ``chrono_name`` before ``columns``.
    This helper accepts both ``(path, columns, chrono_name)`` and
    ``(path, chrono_name, columns)`` for backward compatibility.
    """

    if isinstance(arg1, str) and arg2 is not None and not isinstance(arg2, str):
        chrono_name = arg1
        columns = arg2
    else:
        columns = arg1
        chrono_name = arg2 if isinstance(arg2, str) else None

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

    # Clean ordering and persist
    df["norm"] = df["raw_name"].astype(str).map(_norm)
    df.sort_values(by=["norm"], inplace=True)
    df.drop_duplicates(subset=["norm"], keep="first", inplace=True)
    df.drop(columns=["norm"], inplace=True)
    df.to_csv(path_ref, index=False, quoting=csv.QUOTE_MINIMAL)
    logger.info("Appended new columns to %s: %s", path_ref, columns)


def _append_new_values(
    path_ref: Path,
    arg1: Iterable[tuple[str, str]] | str,
    arg2: Iterable[tuple[str, str]] | str | None = None,
) -> None:
    """Append unknown values to ``path_ref`` CSV with placeholder.

    Like :func:`_append_new_columns`, this function accepts both
    ``(path, rows, chrono_name)`` and ``(path, chrono_name, rows)`` call orders.
    """

    if isinstance(arg1, str) and arg2 is not None and not isinstance(arg2, str):
        chrono_name = arg1
        rows = arg2
    else:
        rows = arg1
        chrono_name = arg2 if isinstance(arg2, str) else None
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

    # Clean ordering and persist
    df["norm_col"] = df["column_name"].astype(str).map(_norm)
    df["norm_val"] = df["raw_value"].astype(str).map(_norm)
    df.sort_values(by=["norm_col", "norm_val"], inplace=True)
    df.drop_duplicates(subset=["norm_col", "norm_val"], keep="first", inplace=True)
    df.drop(columns=["norm_col", "norm_val"], inplace=True)
    df.to_csv(path_ref, index=False, quoting=csv.QUOTE_MINIMAL)
    logger.info("Appended new values to %s: %s entries", path_ref, len(rows))


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
    logger.debug("Applying mappings to dataframe with columns: %s", list(df.columns))

    # Convert provided mapping to use normalized keys for internal processing
    norm_map = { _norm(k): v for k, v in column_map.items() }

    # Verify and append new columns if needed
    unknown_cols = [c for c in df.columns if _norm(c) not in norm_map]
    if unknown_cols:
        _append_new_columns(columns_file, unknown_cols, chrono_name)
        logger.warning("Unknown columns encountered, appended for manual mapping: %s", unknown_cols)
        raise StopIteration("Nouveau nom de colonne à mapper")

    # Determine rename and drop actions
    rename: Dict[str, str] = {}
    drop_cols: list[str] = []
    for col in df.columns:
        mapped = norm_map.get(_norm(col))
        if mapped == "__DROP__":
            drop_cols.append(col)
            # history logging could be added here if needed
        else:
            rename[col] = mapped

    # Apply column renaming and dropping
    df = df.rename(columns=rename)
    if drop_cols:
        df.drop(columns=drop_cols, inplace=True)

    # Normalise value mapping keys for lookups
    norm_val_map = {
        _norm(col): { _norm(k): v for k, v in vals.items() }
        for col, vals in value_map.items()
    }

    # Replace values per column mapping
    for col in list(df.columns):
        mapping = norm_val_map.get(_norm(col))
        if not mapping:
            continue

        new_vals: list[str] = []

        def convert(val: object) -> object:
            if pd.isna(val) or str(val).strip() == "":
                return pd.NA
            raw = str(val)
            norm_raw = _norm(raw)
            if norm_raw not in mapping:
                new_vals.append(raw)
                return pd.NA
            mapped_val = mapping[norm_raw]
            return pd.NA if mapped_val == "" else mapped_val

        df[col] = df[col].map(convert)

        if new_vals:
            _append_new_values(values_file, [(col, v) for v in new_vals], chrono_name)
            logger.warning("Unknown values for column '%s' appended for manual mapping: %s", col, new_vals)
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
        counts = {}
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


def clean_data(
    df: pd.DataFrame,
    *,
    chrono_rank: int = 1,
    column_map: Dict[str, str] | None = None,
    value_map: Dict[str, Dict[str, str]] | None = None,
    columns_file: Path | None = None,
    values_file: Path | None = None,
    chrono_name: str | None = None,
    history_file: Path | None = None,
) -> pd.DataFrame:
    """Return ``df`` cleaned, optionally using manual mappings."""
    df = unmerge_cells(df)
    df = drop_empty_rows(df)
    df = drop_empty_cols(df)
    df = remove_parasitic_rows(df)
    df.reset_index(drop=True, inplace=True)

    if (
        column_map is not None
        and columns_file is not None
        and values_file is not None
    ):
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
