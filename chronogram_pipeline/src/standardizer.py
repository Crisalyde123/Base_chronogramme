"""Header standardization utilities with optional Mistral AI fallback."""

from __future__ import annotations
import os
from pathlib import Path
from typing import Callable, Iterable, List, Mapping, Dict

import pandas as pd
import requests
import yaml

from .logger import get_logger
from .mapping_utils import normalize_text

logger = get_logger(__name__)

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
    df = pd.DataFrame(list(mapping.items()), columns=["En-tête original", "En-tête standard"])
    mapping_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(mapping_csv, index=False, encoding="utf-8")


def _load_schema(schema_path: Path | None) -> List[str]:
    if schema_path and schema_path.exists():
        data = yaml.safe_load(schema_path.read_text())
        fields = [f.get("name") for f in data.get("fields", [])]
        return [str(f) for f in fields if f]
    return []


def _default_mistral_call(header: str, allowed: Iterable[str]) -> str:
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
    resp = requests.post("https://api.mistral.ai/v1/chat/completions", headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()


def standardize_headers_rules(
    headers_list: Iterable[str],
    *,
    mapping_csv: Path,
    log_xlsx: Path | None = None,
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

    if log_xlsx:
        if log_xlsx.exists():
            df_log = pd.read_excel(log_xlsx)
        else:
            df_log = pd.DataFrame(
                columns=["En-tête original", "En-tête standard", "Méthode"]
            )
        for row in log_rows:
            df_log.loc[len(df_log)] = row
        df_log.to_excel(log_xlsx, index=False)

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

    if log_xlsx:
        if log_xlsx.exists():
            df_log = pd.read_excel(log_xlsx)
        else:
            df_log = pd.DataFrame(columns=["En-tête original", "En-tête standard", "Méthode"])
        for row in log_rows:
            df_log.loc[len(df_log)] = row
        df_log.to_excel(log_xlsx, index=False)

    for orig, std, method in log_rows:
        logger.info("Header '%s' -> '%s' via %s", orig, std, method)

    return result

