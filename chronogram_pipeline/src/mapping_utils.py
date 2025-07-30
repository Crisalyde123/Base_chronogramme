"""Utility functions for enriching mapping_values.csv from Excel files."""

from __future__ import annotations

import logging
import unicodedata
from pathlib import Path
from typing import Dict, Iterable, List

import pandas as pd

logger = logging.getLogger(__name__)


def normalize_text(text: str) -> str:
    """Return a lowercase, accent-free version of `text`."""
    if text is None:
        return ""
    text = str(text).strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return text.lower()


def load_header_mapping(path: Path) -> Dict[str, str]:
    """Load header mapping CSV into a dictionary with normalized keys/values."""
    mapping: Dict[str, str] = {}
    if not path.exists():
        logger.warning("Header mapping file %s not found", path)
        return mapping
    df = pd.read_csv(path)
    for _, row in df.iterrows():
        orig = normalize_text(row[0])
        std = normalize_text(row[1])
        mapping[orig] = std
    return mapping


def detect_main_sheet(file: Path) -> str:
    """Return the sheet name with the most non-empty cells."""
    xls = pd.ExcelFile(file)
    best_sheet = xls.sheet_names[0]
    max_count = -1
    for sheet in xls.sheet_names:
        df = xls.parse(sheet, header=None)
        count = int(df.count().sum())
        if count > max_count:
            max_count = count
            best_sheet = sheet
    logger.debug("%s -> main sheet '%s'", file.name, best_sheet)
    return best_sheet


def find_header_row(df: pd.DataFrame, keywords: Iterable[str]) -> int:
    """Return index of row likely containing column headers."""
    for idx, row in df.iterrows():
        values = [normalize_text(v) for v in row]
        matches = sum(any(k in val for val in values) for k in keywords)
        if matches >= 2:
            return idx
    return 0


def extract_table(file: Path, sheet: str) -> pd.DataFrame:
    """Extract main data table from *sheet* of *file*."""
    df_raw = pd.read_excel(file, sheet_name=sheet, header=None)
    header_row = find_header_row(df_raw, ["emetteur", "destinataire", "modalite", "type", "nature"])
    df = pd.read_excel(file, sheet_name=sheet, header=header_row)
    df.dropna(axis=1, how="all", inplace=True)
    return df


def standardize_headers(df: pd.DataFrame, mapping: Dict[str, str]) -> None:
    """Rename DataFrame columns using mapping after normalization."""
    new_cols: List[str] = []
    for col in df.columns:
        norm = normalize_text(col)
        new_cols.append(mapping.get(norm, norm))
    df.columns = new_cols


def canonical_column(name: str) -> str | None:
    """Map normalized column name to canonical target column."""
    name = normalize_text(name)
    if "emetteur" in name:
        return "emetteur"
    if "destinataire" in name:
        return "destinataire"
    if "modalite" in name:
        return "modalite"
    if "type" in name or "nature" in name:
        return "type_inject"
    return None


def enrich_mapping_values(input_dir: Path, header_map_path: Path, values_path: Path, limit: int = 3) -> None:
    """Process Excel files in *input_dir* and update mapping_values.csv."""
    mapping = load_header_mapping(header_map_path)
    values_df = pd.read_csv(values_path)
    existing = set(zip(values_df["Colonne"], values_df["Valeur brute"]))
    added_lines = 0
    cols_inspected = 0

    files = sorted(input_dir.glob("*.xlsx"))[:limit]
    for file in files:
        sheet = detect_main_sheet(file)
        df = extract_table(file, sheet)
        standardize_headers(df, mapping)
        for col in list(df.columns):
            canon = canonical_column(col)
            if canon is None:
                continue
            cols_inspected += 1
            uniques = pd.Series(df[col].dropna().unique()).astype(str).str.strip()
            for val in uniques:
                key = (canon, val)
                if key not in existing:
                    values_df.loc[len(values_df)] = [canon, val, ""]
                    existing.add(key)
                    added_lines += 1
    values_df.drop_duplicates(inplace=True)
    values_df.to_csv(values_path, index=False)
    logger.info("%d columns inspected", cols_inspected)
    logger.info("%d new raw values added", added_lines)
    logger.info("%d total lines now in %s", len(values_df), values_path)
