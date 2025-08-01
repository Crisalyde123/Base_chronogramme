import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data_cleaner import clean_data, unmerge_cells


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


def test_unmerge_cells_series_forward_fill():
    raw = pd.DataFrame({
        "A": ["val1", None, None],
        "B": [None, None, "val2"],
    })

    # Call directly on a Series to emulate intermediate processing
    series_input = raw.loc[0]
    out = unmerge_cells(series_input)
    assert isinstance(out, pd.DataFrame)
    # Horizontal propagation should duplicate the value on the row
    assert list(out.iloc[0]) == ["val1", "val1"]

