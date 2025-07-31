import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data_cleaner import clean_data


def test_clean_data_removes_noise():
    df = pd.DataFrame(
        [
            ["H1", "H2", "Empty"],
            ["val1", "val2", ""],
            ["TOTAL", "", ""],
            ["phase 1", "", ""],
            [None, None, None],
        ]
    )

    out = clean_data(df)

    # Header row plus one data row should remain
    assert out.shape == (2, 2)
    assert list(out.iloc[0]) == ["H1", "H2"]
    assert list(out.iloc[1]) == ["val1", "val2"]
