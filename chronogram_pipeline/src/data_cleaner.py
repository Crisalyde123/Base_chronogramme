"""Data cleaning utilities for chronogram tables."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List
import csv

import pandas as pd

from .mapping_utils import normalize_text


def _log_history(path: Path, rows: List[Dict[str, str]]) -> None:
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
    """Return column name mapping from CSV file at ``path_ref`` and purge applied lines."""
    if not path_ref.exists():
        pd.DataFrame(columns=["chronogramme", "raw_name", "mapped_name"]).to_csv(
            path_ref, index=False, quoting=csv.QUOTE_MINIMAL
        )
        return {}

    df = pd.read_csv(path_ref, dtype=str)
    df.drop_duplicates(subset=["raw_name"], keep="first", inplace=True)

    mapping: Dict[str, str] = {}
    keep_rows = []
    history: List[Dict[str, str]] = []
    for _, row in df.iterrows():
        raw = row.get("raw_name")
        mapped = row.get("mapped_name")
        chrono = row.get("chronogramme", "")
        if pd.isna(raw):
            continue
        raw = str(raw)
        mapped_val = "" if pd.isna(mapped) else str(mapped)
        if mapped_val == "X":
            keep_rows.append(row)
            continue
        if mapped_val in ("", "__DROP__"):
            mapping[raw] = "__DROP__"
        else:
            mapping[raw] = mapped_val
        history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "chronogramme": chrono,
                "category": "column",
                "column": raw,
                "raw": raw,
                "mapped": mapping[raw],
            }
        )

    pd.DataFrame(keep_rows, columns=df.columns).to_csv(
        path_ref, index=False, quoting=csv.QUOTE_MINIMAL
    )
    if history_file is not None:
        _log_history(history_file, history)

    return mapping


def load_value_mapping(path_ref: Path, history_file: Path | None = None) -> Dict[str, Dict[str, str]]:
    """Return per-column value mapping from CSV and purge applied lines."""
    if not path_ref.exists():
        pd.DataFrame(
            columns=["chronogramme", "column_name", "raw_value", "mapped_value"]
        ).to_csv(path_ref, index=False, quoting=csv.QUOTE_MINIMAL)
        return {}

    df = pd.read_csv(path_ref, dtype=str)
    df.drop_duplicates(subset=["column_name", "raw_value"], keep="first", inplace=True)

    mapping: Dict[str, Dict[str, str]] = {}
    keep_rows = []
    history: List[Dict[str, str]] = []
    for _, row in df.iterrows():
        col = row.get("column_name")
        raw = row.get("raw_value")
        mapped = row.get("mapped_value")
        chrono = row.get("chronogramme", "")
        if pd.isna(col) or pd.isna(raw):
            continue
        col = str(col)
        raw = str(raw)
        mapped_val = "" if pd.isna(mapped) else str(mapped)
        if mapped_val == "X":
            keep_rows.append(row)
            continue
        if mapped_val == "__EMPTY__" or mapped_val == "":
            final_val = ""
        else:
            final_val = mapped_val
        mapping.setdefault(col, {})[raw] = final_val
        history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "chronogramme": chrono,
                "category": "value",
                "column": col,
                "raw": raw,
                "mapped": final_val,
            }
        )

    pd.DataFrame(keep_rows, columns=df.columns).to_csv(
        path_ref, index=False, quoting=csv.QUOTE_MINIMAL
    )
    if history_file is not None:
        _log_history(history_file, history)

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


def _append_new_columns(path_ref: Path, chronogramme: str, columns: Iterable[str]) -> None:
    """Append unknown column names to ``path_ref`` CSV with placeholder."""
    if path_ref.exists():
        df = pd.read_csv(path_ref, dtype=str)
    else:
        df = pd.DataFrame(columns=["chronogramme", "raw_name", "mapped_name"])

    existing = set(df.get("raw_name", []))
    for col in columns:
        if col not in existing:
            df.loc[len(df)] = {
                "chronogramme": chronogramme,
                "raw_name": col,
                "mapped_name": "X",
            }
            existing.add(col)

    df.drop_duplicates(subset=["raw_name"], keep="first", inplace=True)
    df.to_csv(path_ref, index=False, quoting=csv.QUOTE_MINIMAL)


def _append_new_values(path_ref: Path, chronogramme: str, rows: Iterable[tuple[str, str]]) -> None:
    """Append unknown values to ``path_ref`` CSV with placeholder."""
    if path_ref.exists():
        df = pd.read_csv(path_ref, dtype=str)
    else:
        df = pd.DataFrame(
            columns=["chronogramme", "column_name", "raw_value", "mapped_value"]
        )

    existing = set(zip(df.get("column_name", []), df.get("raw_value", [])))
    for col, val in rows:
        if (col, val) not in existing:
            df.loc[len(df)] = {
                "chronogramme": chronogramme,
                "column_name": col,
                "raw_value": val,
                "mapped_value": "X",
            }
    df.drop_duplicates(subset=["column_name", "raw_value"], keep="first", inplace=True)
    df.to_csv(path_ref, index=False, quoting=csv.QUOTE_MINIMAL)


def _apply_mappings(
    df: pd.DataFrame,
    column_map: Dict[str, str],
    value_map: Dict[str, Dict[str, str]],
    *,
    columns_file: Path,
    values_file: Path,
    chronogramme: str,
    history_file: Path | None = None,
) -> pd.DataFrame:
    """Rename columns and replace values using provided mappings."""
    df = df.copy()

    unknown_cols = [c for c in df.columns if c not in column_map]
    if unknown_cols:
        _append_new_columns(columns_file, chronogramme, unknown_cols)
        raise StopIteration("Nouveau nom de colonne à mapper")

    rename: Dict[str, str] = {}
    drop_cols = []
    for col in df.columns:
        mapped = column_map.get(col)
        if mapped == "__DROP__":
            drop_cols.append(col)
            if history_file is not None:
                _log_history(
                    history_file,
                    [
                        {
                            "timestamp": datetime.now().isoformat(),
                            "chronogramme": chronogramme,
                            "category": "column",
                            "column": col,
                            "raw": col,
                            "mapped": "__DROP__",
                        }
                    ],
                )
        else:
            rename[col] = mapped
            if history_file is not None and col != mapped:
                _log_history(
                    history_file,
                    [
                        {
                            "timestamp": datetime.now().isoformat(),
                            "chronogramme": chronogramme,
                            "category": "column",
                            "column": col,
                            "raw": col,
                            "mapped": mapped,
                        }
                    ],
                )

    df = df.rename(columns=rename)
    if drop_cols:
        df.drop(columns=drop_cols, inplace=True)

    for col in list(df.columns):
        mapping = value_map.get(col)
        if not mapping:
            continue
        new_vals: List[str] = []
        used_pairs: List[tuple[str, str]] = []

        def convert(val: object) -> object:
            if pd.isna(val) or str(val).strip() == "":
                return pd.NA
            raw = str(val)
            if raw not in mapping:
                if raw not in new_vals:
                    new_vals.append(raw)
                return pd.NA
            mapped_val = mapping[raw]
            used_pairs.append((raw, mapped_val))
            return "" if mapped_val == "" else mapped_val

        df[col] = df[col].map(convert)

        if new_vals:
            _append_new_values(values_file, chronogramme, [(col, v) for v in new_vals])
            raise StopIteration("Nouvelles valeurs à mapper")

        if history_file is not None and used_pairs:
            _log_history(
                history_file,
                [
                    {
                        "timestamp": datetime.now().isoformat(),
                        "chronogramme": chronogramme,
                        "category": "value",
                        "column": col,
                        "raw": r,
                        "mapped": m,
                    }
                    for r, m in used_pairs
                ],
            )

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
    chronogramme: str | None = None,
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
        and chronogramme is not None
    ):
        df = _apply_mappings(
            df,
            column_map,
            value_map or {},
            columns_file=columns_file,
            values_file=values_file,
            chronogramme=chronogramme,
            history_file=history_file,
        )

    df = standardize_and_clean(df, chrono_rank=chrono_rank)
    return df
