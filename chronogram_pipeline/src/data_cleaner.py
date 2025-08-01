"""Data cleaning utilities for chronogram tables."""

from __future__ import annotations

import pandas as pd


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


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Return ``df`` cleaned from empty/parasitic rows and columns."""
    df = unmerge_cells(df)
    df = drop_empty_rows(df)
    df = drop_empty_cols(df)
    df = remove_parasitic_rows(df)
    df.reset_index(drop=True, inplace=True)
    return df
