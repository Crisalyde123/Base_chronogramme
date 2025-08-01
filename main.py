from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable

import pandas as pd

# Import directly from the package so that `main` can be executed as a
# standalone script without being part of a package.  Using an absolute import
# avoids the "attempted relative import with no known parent package" error
# when ``main`` is executed from the repository root or via the helper scripts.
from chronogram_pipeline.src.mapping_utils import normalize_text
from chronogram_pipeline.src.excel_parser import detect_main_sheet
from chronogram_pipeline.src.db_utils import (
    DEFAULT_DB,
    create_connection,
    init_tables,
    insert_chronogram_metadata,
    insert_injects,
)


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


def load_metadata_table(path_ref: Path) -> Dict[str, Dict[str, str]]:
    """Return metadata keyed by file name from CSV at ``path_ref``."""
    if not path_ref.exists():
        return {}
    df = pd.read_csv(path_ref, dtype=str)
    df.fillna("", inplace=True)
    records: Dict[str, Dict[str, str]] = {}
    for _, row in df.iterrows():
        file_name = str(row.get("nom_fichier", ""))
        if not file_name:
            continue
        rec = {
            "nom_chronogramme": row.get("nom_chronogramme", ""),
            "date_exercice": row.get("date_exercice", ""),
            "lieu_exercice": row.get("lieu_exercice", ""),
            "etablissement_nom": row.get("etablissement_nom", ""),
            "etablissement_type": row.get("etablissement_type", ""),
            "submitter": row.get("submitter", ""),
        }
        records[file_name] = rec
    return records


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
    drop_cols: list[str] = []
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


def run_pipeline(
    excel_path: Path | str,
    *,
    config_dir: Path | None = None,
    log_dir: Path | None = None,
    db_path: Path | None = None,
    metadata_csv: Path | None = None,
) -> dict:
    """Execute the minimal chronogram processing pipeline on ``excel_path``.

    This helper loads the Excel file, cleans the data using ``clean_data`` and
    inserts the result into the SQLite database using functions from
    ``chronogram_pipeline.src.db_utils``.  It mirrors the simplified behaviour
    defined in the tests and is intentionally lightweight.

    Parameters
    ----------
    excel_path : Path | str
        Location of the Excel file to process.
    config_dir : Path, optional
        Unused placeholder kept for API compatibility.
    log_dir : Path, optional
        Directory where log files should be written.  The directory is created
        if it does not exist.
    db_path : Path, optional
        SQLite database path. Defaults to ``DEFAULT_DB`` from ``db_utils``.
    metadata_csv : Path, optional
        CSV file containing metadata for input Excel files.

    Returns
    -------
    dict
        Mapping containing the raw ``df``, the ``clean_df`` and the generated
        ``chrono_id``.
    """

    excel_path = Path(excel_path)
    if not excel_path.exists():
        raise FileNotFoundError(f"{excel_path!r} does not exist")
    if excel_path.suffix.lower() != ".xlsx":
        raise ValueError("Input file must be a .xlsx Excel file")

    # default directories relative to this file
    base_dir = Path(__file__).resolve().parent
    config_dir = Path(config_dir) if config_dir else base_dir / "config"
    log_dir = Path(log_dir) if log_dir else base_dir / "data" / "control"
    log_dir.mkdir(parents=True, exist_ok=True)

    db_path = Path(db_path) if db_path else DEFAULT_DB

    # Load Excel and standardize column headers/values using config mappings
    sheet = detect_main_sheet(excel_path)
    df = pd.read_excel(excel_path, sheet_name=sheet)

    headers_csv = config_dir / "mapping_headers.csv"
    values_csv = config_dir / "mapping_values.csv"

    if headers_csv.exists():
        headers_df = pd.read_csv(headers_csv, dtype=str)
        header_map = {
            str(o): str(s)
            for o, s in zip(
                headers_df.get("En-tete original", []),
                headers_df.get("En-tete standard", []),
            )
            if str(o) and str(s)
        }
        if header_map:
            df = df.rename(columns=header_map)

            # merge duplicate columns produced by the mapping
            for col in list({c for c in df.columns if list(df.columns).count(c) > 1}):
                dupes = [c for c in df.columns if c == col]
                base = dupes[0]
                for d in dupes[1:]:
                    df[base] = df[base].fillna(df[d])
                df.drop(columns=dupes[1:], inplace=True)

    value_map: Dict[str, Dict[str, str]] = {}
    if values_csv.exists():
        values_df = pd.read_csv(values_csv, dtype=str)
        for _, row in values_df.iterrows():
            col = str(row.get("Colonne", ""))
            raw = str(row.get("Valeur brute", ""))
            std = str(row.get("Valeur standard", ""))
            if col and raw:
                value_map.setdefault(col, {})[raw] = std
        for col, mapping in value_map.items():
            if col in df.columns:
                df[col] = df[col].map(lambda v: mapping.get(str(v).strip(), v))

    clean_df = clean_data(
        df,
        chrono_rank=1,
    )

    column_renames = {
        "phase": "phase_exercice",
        "type": "type_inject",
        "nature": "modalite",
        "resume": "description",
        "commentaires": "observations",
    }
    for src, dest in column_renames.items():
        if src in clean_df.columns and dest not in clean_df.columns:
            clean_df = clean_df.rename(columns={src: dest})

    if clean_df.empty:
        # Ensure tables exist for the test expectations
        with create_connection(db_path) as conn:
            init_tables(conn)
        raise StopIteration("No injects found")

    metadata_csv = Path(metadata_csv) if metadata_csv else base_dir / "metadata.csv"
    metadata_table = load_metadata_table(metadata_csv)

    if excel_path.name not in metadata_table:
        raise ValueError(f"Metadata for {excel_path.name} not found in {metadata_csv}")

    metadata = metadata_table[excel_path.name].copy()
    metadata.update({
        "nom_fichier_excel": excel_path.name,
        "nb_injects": len(clean_df),
    })

    chrono_id = insert_chronogram_metadata(metadata, db_path=db_path)
    insert_injects(clean_df.assign(id_chronogramme=chrono_id), db_path=db_path)

    return {"df": df, "clean_df": clean_df, "chrono_id": chrono_id}
