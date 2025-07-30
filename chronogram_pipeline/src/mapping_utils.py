import logging
from pathlib import Path
from typing import Iterable, List, Tuple

import openpyxl
import pandas as pd

logger = logging.getLogger(__name__)


def detect_main_sheet(workbook_path: Path) -> openpyxl.worksheet.worksheet.Worksheet:
    """Return the worksheet with the highest number of non-empty cells."""
    wb = openpyxl.load_workbook(workbook_path, data_only=True)
    best_sheet = wb.worksheets[0]
    max_count = -1
    for ws in wb.worksheets:
        count = sum(
            1
            for row in ws.iter_rows(values_only=True)
            for cell in row
            if cell not in (None, "")
        )
        if count > max_count:
            best_sheet = ws
            max_count = count
    logger.info("Selected sheet '%s' with %d cells from %s", best_sheet.title, max_count, workbook_path)
    return best_sheet


def find_data_table(sheet: openpyxl.worksheet.worksheet.Worksheet) -> Tuple[int, int, int]:
    """Return header row index and start/end columns of the data table."""
    for idx, row in enumerate(sheet.iter_rows(values_only=True), start=1):
        values = [cell for cell in row if cell not in (None, "")]
        if len(values) >= 3:
            first_col = next(i for i, c in enumerate(row, start=1) if c not in (None, ""))
            last_col = len(row) - next(i for i, c in enumerate(reversed(row), start=1) if c not in (None, "")) + 1
            logger.info("Header row detected at line %d", idx)
            return idx, first_col, last_col
    raise ValueError("No header row found")


def extract_headers(sheet: openpyxl.worksheet.worksheet.Worksheet, header_row: int, first_col: int, last_col: int) -> List[str]:
    cells = sheet.iter_rows(min_row=header_row, max_row=header_row, min_col=first_col, max_col=last_col, values_only=True)
    headers = []
    for row in cells:
        for value in row:
            if value not in (None, ""):
                headers.append(str(value).strip())
    return headers


def update_mapping_headers(input_dir: Path, mapping_csv: Path, max_files: int = 3) -> Tuple[int, int]:
    """Update mapping CSV with headers extracted from Excel files.

    Returns (total_headers_found, new_headers_added).
    """
    excel_files = [p for p in input_dir.iterdir() if p.suffix.lower() in {".xlsx", ".xls"}]
    excel_files.sort()
    if not excel_files:
        logger.warning("No Excel files found in %s", input_dir)
        return 0, 0
    excel_files = excel_files[:max_files]

    all_headers: List[str] = []
    for file in excel_files:
        sheet = detect_main_sheet(file)
        header_row, first_col, last_col = find_data_table(sheet)
        headers = extract_headers(sheet, header_row, first_col, last_col)
        logger.info("%s -> %d headers", file, len(headers))
        all_headers.extend(headers)

    total_headers = len(all_headers)
    headers_set = {h for h in all_headers if h}

    if mapping_csv.exists() and mapping_csv.stat().st_size > 0:
        df = pd.read_csv(mapping_csv)
    else:
        df = pd.DataFrame(columns=["En-tête original", "En-tête standard"])

    existing = set(df["En-tête original"].astype(str))
    new_entries = [h for h in headers_set if h not in existing]
    for header in new_entries:
        df.loc[len(df)] = [header, ""]

    if new_entries:
        df.to_csv(mapping_csv, index=False)
    logger.info("%d headers extracted, %d new entries added", total_headers, len(new_entries))
    return total_headers, len(new_entries)
