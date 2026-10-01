"""Run the whole pipeline locally (no Databricks) and write gold tables to data/gold/*.parquet.

Same transforms as the Databricks notebooks. Useful as an offline fallback for Power BI and
for the assistant's local mode.
    PYTHONPATH=. uv run --python 3.11 --with pyspark==3.5.3 --with pandas --with pyarrow --with scikit-learn scripts/run_local.py
"""
import json
from datetime import timedelta
from pathlib import Path

from pyspark.sql import SparkSession

from retail import churn, transforms as t

DATA = Path(__file__).resolve().parents[1] / "data"
HORIZON = 90


def main() -> None:
    spark = (SparkSession.builder.master("local[*]").config("spark.sql.ansi.enabled", "true")
             .config("spark.sql.shuffle.partitions", "8")  # laptop-sized; Databricks tunes this itself
             .config("spark.ui.showConsoleProgress", "false")
             .config("spark.driver.memory", "4g").getOrCreate())
    labelled = t.label_rows(spark.read.parquet(str(DATA / "online_retail_ii.parquet"))).cache()
    silver = t.to_silver(labelled).cache()

    max_date = silver.agg({"invoice_date": "max"}).first()[0]
    score_at = max_date + timedelta(days=1)
    test_at, train_at = score_at - timedelta(days=HORIZON), score_at - timedelta(days=2 * HORIZON)

    train_snap = t.churn_snapshot(silver, str(train_at), HORIZON).toPandas()
    test_snap = t.churn_snapshot(silver, str(test_at), HORIZON).toPandas()
    metrics = churn.evaluate(churn.train(train_snap), test_snap)

    model = churn.train(test_snap)  # refit on the most recent labelled snapshot
    current = t.rfm_segments(t.customer_features(silver, str(score_at))).toPandas()
    active = current[current["recency_days"] <= t.ACTIVE_WINDOW_DAYS]

    gold = DATA / "gold"
    gold.mkdir(exist_ok=True)
    t.monthly_kpis(silver).toPandas().to_parquet(gold / "gold_monthly_kpis.parquet", index=False)
    t.product_performance(silver).toPandas().to_parquet(gold / "gold_product_performance.parquet", index=False)
    current.to_parquet(gold / "gold_customer_rfm.parquet", index=False)
    churn.score(model, active).to_parquet(gold / "gold_customer_churn_risk.parquet", index=False)

    reasons = {r["reject_reason"]: r["count"] for r in labelled.groupBy("reject_reason").count().collect()}
    print(json.dumps({"rows_by_reject_reason": reasons, "train_at": str(train_at), "test_at": str(test_at),
                      "score_at": str(score_at), "out_of_time_metrics": metrics}, indent=2, default=str))
    spark.stop()


if __name__ == "__main__":
    main()
