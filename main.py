# Entry point for chronogram pipeline
import os
from pathlib import Path
from datetime import datetime
import pandas as pd
import openpyxl
import yaml

from chronogram_pipeline.src import (
    data_cleaner,
    excel_parser,
    standardizer,
    db_utils,
    mapping_utils,
    PipelineLogger,
    enrich_data,
)
from chronogram_pipeline.src.logger import get_logger


def _latest_xlsx(inputs_dir: Path) -> Path:
    files = [p for p in inputs_dir.glob("*.xlsx") if p.is_file()]
    if not files:
        raise FileNotFoundError(f"No .xlsx files found in {inputs_dir}")
    return max(files, key=lambda p: p.stat().st_mtime)


def _load_allowed(schema_path: Path | None) -> dict:
    if not schema_path or not schema_path.exists():
        return {}
    data = yaml.safe_load(schema_path.read_text()) or {}
    allowed = {}
    for field in data.get("fields", []):
        vals = field.get("values")
        if vals:
            allowed[str(field.get("name"))] = [str(v) for v in vals]
    return allowed


def standardize_column_values(df: pd.DataFrame, mapping_csv: Path, *, schema_path: Path | None = None) -> pd.DataFrame:
    df = df.copy()
    mapping = (
        pd.read_csv(mapping_csv)
        if mapping_csv.exists() and mapping_csv.stat().st_size > 0
        else pd.DataFrame(columns=["Colonne", "Valeur brute", "Valeur standard"])
    )
    allowed = _load_allowed(schema_path)
    for col in df.columns:
        sub = mapping[mapping["Colonne"] == col]
        if not sub.empty:
            replace = dict(zip(sub["Valeur brute"].astype(str), sub["Valeur standard"].astype(str)))
            df[col] = df[col].astype(str).replace(replace)
        if col in allowed:
            df[col] = df[col].astype(str)
            df = df[df[col].isin(allowed[col])]
    return df.reset_index(drop=True)


def run_pipeline(
    xlsx_path: str | Path | None = None,
    *,
    config_dir: Path | None = None,
    log_dir: Path | None = None,
    db_path: Path | None = None,
    logger_name: str | None = None,
):
    if config_dir is None:
        config_dir = Path(__file__).resolve().parent / "chronogram_pipeline" / "config"
    else:
        config_dir = Path(config_dir)
    mapping_headers = config_dir / "mapping_headers.csv"
    mapping_values = config_dir / "mapping_values.csv"
    schema_yaml = config_dir / "schema_definition.yaml"

    if log_dir is not None:
        os.environ["CHRONO_LOG_DIR"] = str(log_dir)
    mapping_log = Path(os.getenv("CHRONO_LOG_DIR", config_dir)) / "mappings_log.xlsx"

    plog = PipelineLogger(logger_name or "main_pipeline")

    with plog.step("SELECT_FILE"):
        inputs_dir = db_utils.BASE_DIR / "data" / "inputs"
        if xlsx_path is None:
            xlsx_file = _latest_xlsx(inputs_dir)
        else:
            xlsx_file = Path(xlsx_path)
        if xlsx_file.suffix.lower() != ".xlsx" or not xlsx_file.exists():
            raise FileNotFoundError(xlsx_file)

    with plog.step("INSERT_METADATA") as m:
        metadata = {
            "nom_chronogramme": xlsx_file.stem,
            "date_exercice": datetime.now().strftime("%Y-%m-%d"),
            "lieu_exercice": "N/A",
            "etablissement_nom": "Auto",
            "etablissement_type": "N/A",
            "submitter": "pipeline",
            "nom_fichier_excel": xlsx_file.name,
        }
        chrono_id = db_utils.insert_chronogram_metadata(metadata, db_path=db_path)
        m["chrono_id"] = chrono_id

    with plog.step("DETECT_SHEET"):
        sheet_name = excel_parser.detect_main_sheet(xlsx_file)

    with plog.step("EXTRACT_RANGE") as m:
        wb = openpyxl.load_workbook(xlsx_file, data_only=True)
        sheet = wb[sheet_name]
        header_row, first_col, last_col = mapping_utils.find_data_table(sheet)
        df_raw = pd.read_excel(
            xlsx_file,
            sheet_name=sheet_name,
            header=header_row - 1,
            usecols=range(first_col - 1, last_col),
        )
        m["rows"] = len(df_raw)

    with plog.step("CLEAN_DATA") as m:
        df_clean = data_cleaner.clean_data(df_raw)
        m["rows"] = len(df_clean)

    with plog.step("STANDARDIZE_HEADERS"):
        try:
            headers = standardizer.standardize_headers(
                df_clean.columns,
                mapping_csv=mapping_headers,
                schema_path=schema_yaml,
                file_name=xlsx_file.stem,
                log_xlsx=mapping_log,
                id_chronogramme=chrono_id,
            )
        except Exception:
            headers = standardizer.standardize_headers_rules(
                df_clean.columns,
                mapping_csv=mapping_headers,
                log_xlsx=mapping_log,
                id_chronogramme=chrono_id,
            )
        df_clean.columns = headers

    with plog.step("STANDARDIZE_VALUES"):
        df_std = standardize_column_values(df_clean, mapping_values, schema_path=schema_yaml)

    with plog.step("ENRICH_DATA") as m:
        df_enriched = enrich_data(
            df_std,
            id_chronogramme=chrono_id,
            etablissement_nom=metadata["etablissement_nom"],
            etablissement_type=metadata["etablissement_type"],
            nom_chronogramme=metadata["nom_chronogramme"],
            date_exercice=metadata["date_exercice"],
        )
        m["rows"] = len(df_enriched)

    with plog.step("INSERT_INJECTS") as m:
        inserted = db_utils.insert_injects(df_enriched, db_path=db_path)
        db_utils.update_chronogram_stats(chrono_id, df_enriched, db_path=db_path)
        m["inserted"] = inserted

    plog.summary()

    log_dir_actual = Path(os.getenv("CHRONO_LOG_DIR", config_dir))
    logs = sorted(log_dir_actual.glob("run_*.log"))
    if not logs:
        default_dir = db_utils.BASE_DIR / "data" / "control"
        logs = sorted(default_dir.glob("run_*.log"))
    log_file = logs[-1] if logs else None

    return {
        "chrono_id": chrono_id,
        "raw_df": df_raw,
        "clean_df": df_clean,
        "df": df_std,
        "enriched_df": df_enriched,
        "log_file": log_file,
        "mapping_log": mapping_log,
    }


def main() -> None:
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Run chronogram pipeline")
    parser.add_argument("file", nargs="?", help="Excel file to process")
    args = parser.parse_args()
    logger = get_logger("main")
    try:
        result = run_pipeline(args.file, logger_name="main")
    except Exception as exc:  # pragma: no cover - CLI handling
        logger.exception("Pipeline failed")
        print(f"\u00c9CHEC : {exc}")
        sys.exit(1)
    else:
        print(f"SUCC\u00c8S : {result['chrono_id']}")
        sys.exit(0)


if __name__ == "__main__":
    main()
