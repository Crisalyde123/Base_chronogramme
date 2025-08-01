import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.correction_tool import csv_to_dict


def test_csv_to_dict_basic(tmp_path):
    data = pd.DataFrame([["A", "Alpha"], ["B", "Beta"]])
    csv_file = tmp_path / "map.csv"
    data.to_csv(csv_file, index=False, header=False)

    result = csv_to_dict(csv_file)

    assert result == {"A": "Alpha", "B": "Beta"}


def test_csv_to_dict_empty_or_single(tmp_path):
    empty_file = tmp_path / "empty.csv"
    pd.DataFrame().to_csv(empty_file, index=False, header=False)
    single_col_file = tmp_path / "single.csv"
    pd.DataFrame([["A"], ["B"]]).to_csv(single_col_file, index=False, header=False)

    assert csv_to_dict(empty_file) == {}
    assert csv_to_dict(single_col_file) == {}
