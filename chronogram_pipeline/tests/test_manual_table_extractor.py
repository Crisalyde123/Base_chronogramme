import sys
from pathlib import Path

# allow imports from project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.manual_table_extractor import (
    detect_header_row,
    detect_last_data_row,
    map_headers,
    STANDARD_FIELDS,
)


def test_detect_header_row_simple():
    lines = [
        ["foo", "bar", "baz"],
        ["Heure", "X", "Descriptif"],
        ["a", "b", "c"],
    ]
    assert detect_header_row(lines) == 1


def test_detect_last_data_row_stops_after_two_blanks():
    lines = [
        ["info"],
        ["Heure", "Descriptif", "Canal"],
        ["t0", "desc", "email"],
        ["t1", "desc2", "sms"],
        ["", "", ""],
        ["", "", ""],
        ["should", "not", "read"],
    ]
    assert detect_last_data_row(lines, 1) == 3


def test_map_headers_known_and_unknown():
    headers = ["Heure", "Descriptif", "Canal", "Autre"]
    result = map_headers(headers)
    expected = [
        ("Heure", STANDARD_FIELDS[0]),
        ("Descriptif", STANDARD_FIELDS[1]),
        ("Canal", STANDARD_FIELDS[4]),
        ("Autre", "Inconnu"),
    ]
    assert result == expected
