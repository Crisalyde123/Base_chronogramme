"""Header standardization utilities with optional Mistral AI fallback."""

from __future__ import annotations
import os
from pathlib import Path
from typing import Callable, Iterable, List, Mapping, Dict
from datetime import datetime, timezone
import csv

import pandas as pd
import requests
import yaml

from .logger import get_logger
from .mapping_utils import normalize_text

logger = get_logger(__name__)

# Default path for the mappings log file
CONTROL_DIR = Path(
    os.getenv("CHRONO_LOG_DIR", Path(__file__).resolve().parents[1] / "data/control")
)
DEFAULT_MAPPING_LOG = CONTROL_DIR / "mappings_log.xlsx"

# Type of the callback used to suggest a header
SuggestFunc = Callable[[str, Iterable[str]], str]


def _load_mapping(mapping_csv: Path) -> Mapping[str, str]:
    """Return header mapping from *mapping_csv* with fallback for legacy encodings."""
    if not (mapping_csv.exists() and mapping_csv.stat().st_size > 0):
        return {}

    try:
        df = pd.read_csv(mapping_csv)
    except UnicodeDecodeError:
        # Some files may be created with the OS default encoding (e.g. Windows
        # cp1252).  Retry with a more permissive codec.
        with mapping_csv.open("r", encoding="latin1") as fh:
            df = pd.read_csv(fh)

    return dict(zip(df.iloc[:, 0].astype(str), df.iloc[:, 1].astype(str)))


def _load_mapping_normalized(mapping_csv: Path) -> Dict[str, str]:
    """Load mapping with normalized keys for rule-based matching."""
    mapping: Dict[str, str] = {}
    if mapping_csv.exists() and mapping_csv.stat().st_size > 0:
        df = pd.read_csv(mapping_csv)
        for _, row in df.iterrows():
            orig = normalize_text(str(row.iloc[0]))
            mapping[orig] = str(row.iloc[1])
    return mapping


def _save_mapping(mapping_csv: Path, mapping: Mapping[str, str]) -> None:
    """Write header ``mapping`` to ``mapping_csv`` in UTF-8."""
    df = pd.DataFrame(
        list(mapping.items()), columns=["En-tête original", "En-tête standard"]
    )
    mapping_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(mapping_csv, index=False, encoding="utf-8", quoting=csv.QUOTE_MINIMAL)


def _load_schema(schema_path: Path | None) -> List[str]:
    """Return list of field names defined in the YAML schema."""
    if schema_path and schema_path.exists():
        data = yaml.safe_load(schema_path.read_text())
        fields = [f.get("name") for f in data.get("fields", [])]
        return [str(f) for f in fields if f]
    return []


def _append_mapping_log(
    rows: Iterable[tuple[str, str, str]],
    log_path: Path,
    *,
    chrono_id: str | None = None,
) -> None:
    """Append mapping *rows* to *log_path* with optional chronogram id."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    columns = [
        "id_chronogramme",
        "nom_original",
        "champ_standard",
        "methode",
        "horodatage",
    ]

    if log_path.exists():
        df_log = pd.read_excel(log_path)
    else:
        df_log = pd.DataFrame(columns=columns)

    for orig, std, method in rows:
        df_log.loc[len(df_log)] = [
            chrono_id if chrono_id is not None else "",
            normalize_text(orig),
            normalize_text(std),
            method,
            timestamp,
        ]

    df_log.to_excel(log_path, index=False)


def _default_mistral_call(header: str, allowed: Iterable[str]) -> str:
    """Call the Mistral API to suggest a standard header."""
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY not set")
    prompt = (
        "En-tête original: "
        + header
        + "\nChamps autorisés: "
        + ", ".join(allowed)
        + "\nPropose uniquement le nom du champ standard le plus pertinent."
    )
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": "mistral-small",
        "messages": [{"role": "user", "content": prompt}],
    }
    resp = requests.post(
        "https://api.mistral.ai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def standardize_headers_rules(
    headers_list: Iterable[str],
    *,
    mapping_csv: Path,
    log_xlsx: Path | None = None,
    id_chronogramme: str | None = None,
) -> List[str]:
    """Standardize headers using only local dictionary rules."""
    mapping = _load_mapping_normalized(mapping_csv)
    result: List[str] = []
    log_rows = []

    for header in headers_list:
        header_str = "" if header is None else str(header).strip()
        if not header_str:
            result.append(header_str)
            continue
        norm = normalize_text(header_str)
        std = mapping.get(norm, "")
        log_rows.append((header_str, std, "règle"))
        result.append(std)

    log_file = log_xlsx or DEFAULT_MAPPING_LOG
    _append_mapping_log(log_rows, log_file, chrono_id=id_chronogramme)

    for orig, std, method in log_rows:
        logger.info("Header '%s' -> '%s' via %s", orig, std, method)

    return result


def standardize_headers(
    headers_list: Iterable[str],
    *,
    mapping_csv: Path,
    schema_path: Path | None = None,
    prompts_dir: Path | None = None,
    gpt_suggest_header: SuggestFunc | None = None,
    file_name: str | None = None,
    log_xlsx: Path | None = None,
    id_chronogramme: str | None = None,
) -> List[str]:
    """Return list of standardized headers using dictionary and optional AI."""
    mapping = _load_mapping(mapping_csv)
    allowed = _load_schema(schema_path)

    prompts_dir = prompts_dir or Path("prompts")
    prompts_dir.mkdir(parents=True, exist_ok=True)
    new_mapping = False
    result: List[str] = []
    log_rows = []

    suggest = gpt_suggest_header or _default_mistral_call

    for header in headers_list:
        header_str = "" if header is None else str(header).strip()
        if not header_str:
            result.append(header_str)
            continue
        if header_str in mapping and mapping[header_str]:
            std = mapping[header_str]
            method = "dict"
        else:
            prompt_text = (
                f"En-tête original: {header_str}\n"
                f"Champs autorisés: {', '.join(allowed)}\n"
                "Instruction: proposer le champ standard le plus pertinent, et uniquement le nom."
            )
            safe_header = header_str.replace("/", "_").replace(" ", "_")
            base = file_name or "file"
            prompt_file = prompts_dir / f"{base}_header_{safe_header}.txt"
            prompt_file.write_text(prompt_text, encoding="utf-8")
            std = suggest(header_str, allowed)
            mapping[header_str] = std
            new_mapping = True
            method = "IA"
            logger.info(
                "IA header mapping",
                extra={
                    "event": "IA_CALL",
                    "type": "header",
                    "prompt": str(prompt_file.name),
                    "response": std,
                },
            )
        log_rows.append((header_str, std, method))
        result.append(std)

    if new_mapping:
        _save_mapping(mapping_csv, mapping)

    log_file = log_xlsx or DEFAULT_MAPPING_LOG
    _append_mapping_log(log_rows, log_file, chrono_id=id_chronogramme)

    for orig, std, method in log_rows:
        logger.info("Header '%s' -> '%s' via %s", orig, std, method)

    return result


def _load_value_mappings(yaml_path: Path) -> Dict[str, Dict[str, str]]:
    """Load per-column value mappings from YAML with normalized keys."""
    if not yaml_path.exists():
        return {}
    data = yaml.safe_load(yaml_path.read_text()) or {}
    mappings: Dict[str, Dict[str, str]] = {}
    for col, vals in data.items():
        mappings[col] = {
            normalize_text(str(k)): str(v) for k, v in (vals or {}).items()
        }
    return mappings


def _save_value_mappings(
    yaml_path: Path, mappings: Mapping[str, Mapping[str, str]]
) -> None:
    """Write ``mappings`` to ``yaml_path`` in YAML format."""
    yaml_path.parent.mkdir(parents=True, exist_ok=True)
    with yaml_path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(mappings, fh, allow_unicode=True)


def _load_allowed_values(schema_path: Path | None) -> Dict[str, List[str]]:
    """Return allowed values per column as defined in ``schema_path``."""
    if not schema_path or not schema_path.exists():
        return {}
    data = yaml.safe_load(schema_path.read_text()) or {}
    allowed: Dict[str, List[str]] = {}
    for field in data.get("fields", []):
        name = field.get("name")
        values = field.get("values")
        if name and values:
            allowed[str(name)] = [str(v) for v in values]
    return allowed


def standardize_values(
    col_name: str,
    series: pd.Series,
    *,
    mappings: Dict[str, Dict[str, str]],
    allowed: Iterable[str] = (),
    mapping_yaml: Path,
    prompts_dir: Path,
    gpt_suggest_value: SuggestFunc | None = None,
    file_name: str | None = None,
    log_xlsx: Path | None = None,
    id_chronogramme: str | None = None,
) -> pd.Series:
    """Standardize values of one column using dictionary and optional AI."""

    mapping = mappings.get(col_name, {})
    prompts_dir.mkdir(parents=True, exist_ok=True)
    suggest = gpt_suggest_value or _default_mistral_call
    new_mapping = False
    result = []
    log_rows = []

    for val in series:
        if pd.isna(val):
            result.append(val)
            continue
        raw = str(val).strip()
        norm = normalize_text(raw)
        if norm in mapping and mapping[norm]:
            std = mapping[norm]
            method = "dict"
        elif raw in allowed:
            std = raw
            method = "ok"
        else:
            prompt_text = (
                f'Dans le champ "{col_name}", comment standardiser la valeur "{raw}" ? '
                f"Liste autorisee : [{', '.join(allowed)}]"
            )
            safe_val = raw.replace("/", "_").replace(" ", "_")
            base = file_name or "file"
            prompt_file = prompts_dir / f"{base}_{col_name}_{safe_val}.txt"
            prompt_file.write_text(prompt_text, encoding="utf-8")
            std = suggest(raw, allowed)
            mapping[norm] = std
            mappings[col_name] = mapping
            new_mapping = True
            method = "IA"
            logger.info(
                "IA value mapping",
                extra={
                    "event": "IA_CALL",
                    "type": "value",
                    "prompt": str(prompt_file.name),
                    "response": std,
                },
            )
        log_rows.append((raw, std, method))
        result.append(std)

    if new_mapping:
        _save_value_mappings(mapping_yaml, mappings)

    log_file = log_xlsx or DEFAULT_MAPPING_LOG
    _append_mapping_log(log_rows, log_file, chrono_id=id_chronogramme)

    for orig, std, method in log_rows:
        logger.info("Value '%s' -> '%s' via %s", orig, std, method)

    return pd.Series(result, index=series.index)


def standardize_column_values(
    df: pd.DataFrame,
    *,
    mapping_yaml: Path,
    schema_path: Path | None = None,
    prompts_dir: Path | None = None,
    gpt_suggest_value: SuggestFunc | None = None,
    file_name: str | None = None,
    log_xlsx: Path | None = None,
    id_chronogramme: str | None = None,
) -> pd.DataFrame:
    """Standardize values of all columns in *df* using mappings and optional AI."""

    mappings = _load_value_mappings(mapping_yaml)
    allowed_all = _load_allowed_values(schema_path)
    prompts_dir = prompts_dir or Path("prompts")

    for col in list(df.columns):
        if col not in mappings and col not in allowed_all:
            continue
        allowed = allowed_all.get(col, [])
        df[col] = standardize_values(
            col,
            df[col],
            mappings=mappings,
            allowed=allowed,
            mapping_yaml=mapping_yaml,
            prompts_dir=prompts_dir,
            gpt_suggest_value=gpt_suggest_value,
            file_name=file_name,
            log_xlsx=log_xlsx,
            id_chronogramme=id_chronogramme,
        )

    return df
