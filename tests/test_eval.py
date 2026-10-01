import datetime as dt

import pandas as pd

from assistant.eval import results_match


def test_matches_despite_renamed_columns_order_and_rounding():
    ref = pd.DataFrame({"country": ["France", "EIRE"], "rev": [100.0, 250.0]})
    got = pd.DataFrame({"total": [250.4, 100.0], "Country": ["EIRE", "France"], "extra": [1, 2]})
    assert results_match(ref, got)


def test_rejects_wrong_numbers_or_row_counts():
    ref = pd.DataFrame({"rev": [100.0]})
    assert not results_match(ref, pd.DataFrame({"rev": [110.0]}))
    assert not results_match(ref, pd.DataFrame({"rev": [100.0, 5.0]}))


def test_dates_compare_across_backends():
    ref = pd.DataFrame({"month": pd.to_datetime(["2011-11-01"])})  # DuckDB returns timestamps
    got = pd.DataFrame({"month": [dt.date(2011, 11, 1)]})  # Databricks returns dates
    assert results_match(ref, got)
