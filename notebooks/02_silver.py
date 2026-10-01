# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Silver — clean, conform, quarantine
# MAGIC Every row gets a `reject_reason`. Clean rows go to **silver**; rejected rows go to **quarantine**
# MAGIC (never silently deleted), so the client can audit exactly what was excluded and why:
# MAGIC
# MAGIC | reason | meaning |
# MAGIC |---|---|
# MAGIC | `non_product_code` | postage, fees, manual adjustments (POST, DOT, M, BANK CHARGES…) |
# MAGIC | `bad_debt_adjustment` | accounting entries (invoice starts with `A`) |
# MAGIC | `zero_or_negative_price` | free samples / data errors |
# MAGIC | `stock_writeoff` | negative quantity that is not a customer cancellation |
# MAGIC | `unparseable` | could not cast quantity / price / date |

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("schema", "retail")
catalog, schema = dbutils.widgets.get("catalog"), dbutils.widgets.get("schema")

import os, sys
sys.path.append(os.path.abspath(".."))
from retail import transforms as t
from retail.tables import save

MIN_RETENTION = 0.90  # fail the job if a source change suddenly rejects >10% of rows

# COMMAND ----------

labelled = t.label_rows(spark.table(f"{catalog}.{schema}.bronze_transactions"))
save(t.to_silver(labelled), f"{catalog}.{schema}.silver_transactions",
     "Clean product sales and cancellations; one row per invoice line, line_value negative for cancellations")
save(t.to_quarantine(labelled), f"{catalog}.{schema}.silver_quarantine",
     "Rows excluded from silver, with reject_reason")

# COMMAND ----------

# MAGIC %md ### Data-quality gate

# COMMAND ----------

report = labelled.groupBy("reject_reason").count().orderBy("count", ascending=False)
display(report)

total = labelled.count()
kept = labelled.filter("reject_reason IS NULL").count()
retention = kept / total
print(f"Kept {kept:,} of {total:,} deduplicated rows ({retention:.1%})")
assert retention >= MIN_RETENTION, f"Data-quality gate failed: only {retention:.1%} of rows passed"
