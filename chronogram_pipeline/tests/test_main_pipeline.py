from pathlib import Path
import pandas as pd
import sqlite3

import src.db_utils as db_utils
from src.form_handler import handle_form_submission


def run_pipeline(
    excel_path: Path | str,
    config_dir: Path | str,
    log_dir: Path | str,
    db_path: Path | str,
) -> dict:
    """
    1. Validate and read the Excel file.
    2. Standardize headers using mapping_headers.csv.
    3. Write a mapping log and a basic run log.
    4. Return both the raw standardized DataFrame and a 'clean' copy.
    5. Initialize the SQLite DB and insert a chronogram record.
    """
    # Resolve paths
    excel_path = Path(excel_path)
    config_dir = Path(config_dir)
    log_dir = Path(log_dir)
    db_path = Path(db_path)

    # 1) Validate input file
    if not excel_path.exists():
        raise FileNotFoundError(f"{excel_path!r} does not exist")
    if excel_path.suffix.lower() != ".xlsx":
        raise ValueError("Input file must be a .xlsx Excel file")

    # 2) Read the Excel into a DataFrame
    df = pd.read_excel(excel_path)

    # 3) Load and apply header mappings
    headers_map_df = pd.read_csv(config_dir / "mapping_headers.csv", dtype=str)
    header_map = {
        orig: std
        for orig, std in zip(
            headers_map_df["En-tete original"], headers_map_df["En-tete standard"]
        )
    }
    df = df.rename(columns=header_map)

    # 4) Ensure log directory exists
    log_dir.mkdir(parents=True, exist_ok=True)

    # 5) Write the header-mapping log
    mapping_log = log_dir / "mapping_log.csv"
    headers_map_df.to_csv(mapping_log, index=False)

    # 6) Write a simple run log
    log_file = log_dir / "pipeline.log"
    log_file.write_text("Pipeline run completed\n")

    # 7) For now, the "clean" DataFrame is just a copy of the standardized one
    clean_df = df.copy()

    # 8) Initialize the SQLite DB (creates tables if needed)
    conn = sqlite3.connect(str(db_path))
    db_utils.init_tables(conn)
    conn.close()

    # 9) Insert a chronogram record to get an ID (minimal defaults)
    form_data = {
        "file_path": str(excel_path),
        "etablissement_nom": "",
        "nom_chronogramme": "",
        "date_exercice": "",
    }
    chrono_id, _ = handle_form_submission(form_data)

    return {
        "df": df,
        "clean_df": clean_df,
        "mapping_log": mapping_log,
        "log_file": log_file,
        "chrono_id": chrono_id,
    }
