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


def load_column_mapping(path_ref: Path) -> Dict[str, str]:
    """Return column name mapping from CSV file at ``path_ref``."""
    if not path_ref.exists():
        # Create an empty mapping file with header, ready for manual mapping
        pd.DataFrame(
            columns=["raw_name", "mapped_name", "nom_chronogramme"]
        ).to_csv(path_ref, index=False, quoting=csv.QUOTE_MINIMAL)
        logger.info("Created column mapping file %s", path_ref)
        return {}

    df = pd.read_csv(path_ref, dtype=str)
    if "nom_chronogramme" not in df.columns:
        df["nom_chronogramme"] = ""

    # Normalize raw names and ensure unique entries
    df["norm"] = df["raw_name"].astype(str).map(_norm)
    df.sort_values(by=["norm"], inplace=True)
    df.drop_duplicates(subset=["norm"], keep="first", inplace=True)
    df.drop(columns=["norm"], inplace=True)

    # Persist cleaned mapping back to CSV
    df.to_csv(path_ref, index=False, quoting=csv.QUOTE_MINIMAL)

    # Build mapping dict: norm(raw_name) -> mapped_name or __DROP__
    mapping: Dict[str, str] = {}
    for _, row in df.iterrows():
        raw = str(row.get("raw_name", ""))
        mapped = "" if pd.isna(row.get("mapped_name")) else str(row.get("mapped_name"))
        if mapped == "XXX":
            # placeholder: skip until manually filled
            continue
        key = _norm(raw)
        mapping[key] = "__DROP__" if mapped == "" else mapped

    logger.debug("Loaded %d column mappings from %s", len(mapping), path_ref)
    return mapping


def load_value_mapping(path_ref: Path) -> Dict[str, Dict[str, str]]:
    """Return per-column value mapping from CSV file at ``path_ref``."""
    if not path_ref.exists():
        pd.DataFrame(
            columns=["column_name", "raw_value", "mapped_value", "nom_chronogramme"]
        ).to_csv(path_ref, index=False, quoting=csv.QUOTE_MINIMAL)
        logger.info("Created value mapping file %s", path_ref)
        return {}

    df = pd.read_csv(path_ref, dtype=str)
    if "nom_chronogramme" not in df.columns:
        df["nom_chronogramme"] = ""

    # Normalize and dedupe per column
    df["norm_col"] = df["column_name"].astype(str).map(_norm)
    df["norm_val"] = df["raw_value"].astype(str).map(_norm)
    df.sort_values(by=["norm_col", "norm_val"], inplace=True)
    df.drop_duplicates(subset=["norm_col", "norm_val"], keep="first", inplace=True)
    df.drop(columns=["norm_col", "norm_val"], inplace=True)

    # Write back cleaned reference
    df.to_csv(path_ref, index=False, quoting=csv.QUOTE_MINIMAL)

    mapping: Dict[str, Dict[str, str]] = {}
    for _, row in df.iterrows():
        col = str(row.get("column_name", ""))
        raw = str(row.get("raw_value", ""))
        mapped = "" if pd.isna(row.get("mapped_value")) else str(row.get("mapped_value"))
        if mapped == "XXX":
            continue
        mapping.setdefault(_norm(col), {})[_norm(raw)] = mapped

    logger.debug("Loaded value mapping for %d columns from %s", len(mapping), path_ref)
    return mapping


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

    # Clean ordering and persist
    df["norm"] = df["raw_name"].astype(str).map(_norm)
    df.sort_values(by=["norm"], inplace=True)
    df.drop_duplicates(subset=["norm"], keep="first", inplace=True)
    df.drop(columns=["norm"], inplace=True)
    df.to_csv(path_ref, index=False, quoting=csv.QUOTE_MINIMAL)
    logger.info("Appended new columns to %s: %s", path_ref, columns)


def _append_new_values(
    path_ref: Path,
    rows: Iterable[tuple[str, str]],
    chrono_name: str | None = None,
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

    # Verify and append new columns if needed
    unknown_cols = [c for c in df.columns if _norm(c) not in column_map]
    if unknown_cols:
        _append_new_columns(columns_file, unknown_cols, chrono_name)
        logger.warning("Unknown columns encountered, appended for manual mapping: %s", unknown_cols)
        raise StopIteration("Nouveau nom de colonne à mapper")

    # Determine rename and drop actions
    rename: Dict[str, str] = {}
    drop_cols: list[str] = []
    for col in df.columns:
        mapped = column_map.get(_norm(col))
        if mapped == "__DROP__":
            drop_cols.append(col)
        else:
            rename[col] = mapped

    # Apply column renaming and dropping
    df = df.rename(columns=rename)
    if drop_cols:
        df.drop(columns=drop_cols, inplace=True)

    # Replace values per column mapping
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
            logger.warning("Unknown values for column '%s' appended for manual mapping: %s", col, new_vals)
            raise StopIteration("Nouvelles valeurs à mapper")

    return df
