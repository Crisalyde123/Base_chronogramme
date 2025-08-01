from __future__ import annotations

import pandas as pd
from pathlib import Path
import yaml

from .logger import get_logger

logger = get_logger(__name__)


def load_schema_fields(schema_path: Path) -> list[str]:
    """Return the list of field names defined in *schema_path*."""
    if not schema_path or not schema_path.exists():
        logger.warning("Schema file %s not found", schema_path)
        return []
    data = yaml.safe_load(schema_path.read_text()) or {}
    fields = [str(f.get("name")) for f in data.get("fields", []) if f.get("name")]
    logger.debug("Loaded %d schema fields from %s", len(fields), schema_path)
    return fields


def apply_schema_columns(df: pd.DataFrame, schema_path: Path) -> pd.DataFrame:
    """Return ``df`` with only columns defined in ``schema_path``.

    Missing columns are created with ``pd.NA`` and the order of columns
    follows the schema definition. If the schema is empty, ``df`` is
    returned unchanged.
    """
    fields = load_schema_fields(schema_path)
    if not fields:
        return df

    result = pd.DataFrame(index=df.index)
    for field in fields:
        if field in df.columns:
            result[field] = df[field]
        else:
            result[field] = pd.NA
    return result
