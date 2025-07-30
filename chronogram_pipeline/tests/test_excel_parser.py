import sys
from pathlib import Path

import openpyxl

# allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.excel_parser import detect_main_sheet


def make_workbook():
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "Data"
    for i in range(3):
        ws1.cell(row=i + 1, column=1, value=i)
    ws2 = wb.create_sheet("Chronogramme")
    ws2.cell(row=1, column=1, value="header")
    wb.create_sheet("Empty")
    return wb


def test_detect_main_sheet_prefers_keyword():
    wb = make_workbook()
    assert detect_main_sheet(wb) == "Chronogramme"


def test_detect_main_sheet_highest_density():
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "Sheet1"
    for i in range(2):
        for j in range(2):
            ws1.cell(row=i + 1, column=j + 1, value=1)
    ws2 = wb.create_sheet("Sheet2")
    for i in range(3):
        for j in range(3):
            if i != 2:
                ws2.cell(row=i + 1, column=j + 1, value=1)
    assert detect_main_sheet(wb) == "Sheet2"


def test_detect_main_sheet_tie_returns_first():
    wb = openpyxl.Workbook()
    ws1 = wb.active
    ws1.title = "A"
    ws1.cell(row=1, column=1, value=1)
    ws2 = wb.create_sheet("B")
    ws2.cell(row=1, column=1, value=1)
    assert detect_main_sheet(wb) == "A"
