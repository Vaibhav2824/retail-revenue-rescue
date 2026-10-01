# Databricks notebook source
# MAGIC %md
# MAGIC # 04 · Churn model — who is about to leave, and what is it worth?
# MAGIC **Churned** = an active customer (bought in the last 12 months) who places **no order in the next 90 days**.
# MAGIC
# MAGIC Validation is **out-of-time**: train on the snapshot 180 days before the data ends, test on the
# MAGIC snapshot 90 days before. A random split would leak future behaviour and flatter the model.
# MAGIC The model must beat the rule the business already uses: *"longest since last order = most at risk"*.

# COMMAND ----------

# MAGIC %pip install -q mlflow scikit-learn

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("schema", "retail")
catalog, schema = dbutils.widgets.get("catalog"), dbutils.widgets.get("schema")

import os, sys
from datetime import timedelta
sys.path.append(os.path.abspath(".."))
import mlflow
from mlflow.models import infer_signature
from retail import churn, transforms as t
from retail.tables import save

HORIZON = 90
silver = spark.table(f"{catalog}.{schema}.silver_transactions")
score_at = silver.agg({"invoice_date": "max"}).first()[0] + timedelta(days=1)
test_at, train_at = score_at - timedelta(days=HORIZON), score_at - timedelta(days=2 * HORIZON)

train_snap = t.churn_snapshot(silver, str(train_at), HORIZON).toPandas()
test_snap = t.churn_snapshot(silver, str(test_at), HORIZON).toPandas()

# COMMAND ----------

mlflow.set_experiment(f"/Users/{spark.sql('SELECT current_user()').first()[0]}/retail-churn")
with mlflow.start_run(run_name="hgb-out-of-time") as run:
    metrics = churn.evaluate(churn.train(train_snap), test_snap)
    mlflow.log_params(churn.PARAMS | {"train_snapshot": str(train_at), "test_snapshot": str(test_at), "horizon_days": HORIZON})
    mlflow.log_metrics(metrics)

    model = churn.train(test_snap)  # refit on the most recent labelled snapshot before scoring
    X = test_snap[churn.FEATURES]
    # MLflow 3 saves sklearn models with skops, which only reloads allow-listed types. TreePredictor is the
    # internal tree of the model we just trained in this run, so trusting it is safe (never do this for downloaded models).
    mlflow.sklearn.log_model(model, name="model", signature=infer_signature(X, model.predict_proba(X)[:, 1]),
                             input_example=X.head(3),
                             skops_trusted_types=["sklearn.ensemble._hist_gradient_boosting.predictor.TreePredictor"])
print(metrics)

# COMMAND ----------

# MAGIC %md ### Score today's active customers → `gold_customer_churn_risk`

# COMMAND ----------

current = t.customer_features(silver, str(score_at)).toPandas()
scored = churn.score(model, current[current["recency_days"] <= t.ACTIVE_WINDOW_DAYS])
scored["model_run_id"] = run.info.run_id  # lineage: every score traces back to its MLflow run
save(spark.createDataFrame(scored), f"{catalog}.{schema}.gold_customer_churn_risk",
     "Active customers scored for 90-day churn: churn_probability, revenue_at_risk (GBP) = probability x revenue_365d")
display(spark.table(f"{catalog}.{schema}.gold_customer_churn_risk").orderBy("revenue_at_risk", ascending=False).limit(20))
