import pandas as pd
import pytest
from pyspark.sql import SparkSession

from retail import churn, transforms as t

COLS = ["invoice", "stock_code", "description", "quantity", "invoice_date", "price", "customer_id", "country"]
ROWS = [
    # clean sales for customer 1 (two orders) and customer 2 (one order, long ago)
    ("100", "85048", "LIGHTS", "10", "2011-01-10 10:00:00", "2.0", "1", "United Kingdom"),
    ("100", "85048", "LIGHTS", "10", "2011-01-10 10:00:00", "2.0", "1", "United Kingdom"),  # exact duplicate
    ("101", "22041", "FRAME", "5", "2011-03-01 09:00:00", "4.0", "1", "United Kingdom"),
    ("102", "22041", "FRAME", "1", "2010-01-01 09:00:00", "4.0", "2", "France"),
    ("C103", "22041", "FRAME", "-2", "2011-03-02 09:00:00", "4.0", "1", "United Kingdom"),  # cancellation
    # rejects
    ("104", "POST", "POSTAGE", "1", "2011-03-01 09:00:00", "18.0", "1", "United Kingdom"),
    ("A105", "B", "Adjust bad debt", "1", "2011-03-01 09:00:00", "100.0", None, "United Kingdom"),
    ("106", "22041", "FRAME", "3", "2011-03-01 09:00:00", "0", None, "United Kingdom"),
    ("107", "22041", "damaged", "-10", "2011-03-01 09:00:00", "4.0", None, "United Kingdom"),
    ("108", "22041", "FRAME", "abc", "2011-03-01 09:00:00", "4.0", None, "United Kingdom"),
    # customer 3 only ever cancelled -> must not divide by zero
    ("C110", "22041", "FRAME", "-1", "2011-03-05 09:00:00", "4.0", "3", "United Kingdom"),
    # customer 1 returns after the snapshot date -> not churned
    ("109", "85048", "LIGHTS", "1", "2011-04-15 09:00:00", "2.0", "1", "United Kingdom"),
]


@pytest.fixture(scope="module")
def spark():
    s = (SparkSession.builder.master("local[1]")
         .config("spark.sql.ansi.enabled", "true")  # Databricks serverless default
         .config("spark.sql.shuffle.partitions", "1").getOrCreate())
    yield s
    s.stop()


@pytest.fixture(scope="module")
def labelled(spark):
    return t.label_rows(spark.createDataFrame(ROWS, COLS)).cache()


def test_every_bad_row_gets_the_right_reason(labelled):
    reasons = {r.invoice: r.reject_reason for r in labelled.collect()}
    assert reasons["104"] == "non_product_code"
    assert reasons["A105"] == "bad_debt_adjustment"
    assert reasons["106"] == "zero_or_negative_price"
    assert reasons["107"] == "stock_writeoff"
    assert reasons["108"] == "unparseable"
    assert reasons["C103"] is None


def test_silver_dedupes_and_signs_line_values(labelled):
    silver = t.to_silver(labelled)
    assert silver.count() == 6  # 12 rows - 1 duplicate - 5 rejects
    assert t.to_quarantine(labelled).count() == 5
    cancel = silver.filter("invoice = 'C103'").first()
    assert cancel.is_cancellation and cancel.line_value == -8.0


def test_monthly_kpis_separates_gross_and_cancelled(labelled):
    mar = t.monthly_kpis(t.to_silver(labelled)).filter("month = '2011-03-01'").first()
    assert (mar.gross_revenue, mar.cancelled_value, mar.net_revenue, mar.orders) == (20.0, 12.0, 8.0, 1)  # cancellations: C103 (8) + C110 (4)


def test_customer_features_ignore_the_future(labelled):
    feats = {r.customer_id: r for r in t.customer_features(t.to_silver(labelled), "2011-04-01").collect()}
    assert "3" not in feats  # cancellation-only customer has no purchase behaviour
    c1 = feats["1"]
    assert c1.frequency == 2  # order 109 is after as_of and must be excluded
    assert c1.monetary == 32.0  # 20 + 20 - 8
    assert c1.recency_days == 31  # last purchase 2011-03-01
    assert c1.cancel_rate == round(8 / 40, 4)


def test_churn_snapshot_labels_and_active_window(labelled):
    snap = {r.customer_id: r.churned for r in t.churn_snapshot(t.to_silver(labelled), "2011-04-01").collect()}
    assert snap == {"1": 0}  # customer 2 last bought >365 days ago -> outside the active base


def test_rfm_segments_assign_every_customer(labelled):
    feats = t.customer_features(t.to_silver(labelled), "2011-04-01")
    assert t.rfm_segments(feats).filter("segment IS NULL").count() == 0


def test_score_revenue_at_risk_is_probability_times_revenue():
    df = pd.DataFrame({f: [1.0, 2.0, 3.0, 4.0] * 5 for f in churn.FEATURES} | {"churned": [0, 1] * 10})
    scored = churn.score(churn.train(df), df)
    assert scored["churn_probability"].between(0, 1).all()
    expected = (scored["churn_probability"] * df["revenue_365d"]).round(2)
    assert (scored["revenue_at_risk"] - expected).abs().max() <= 0.01
