# Databricks notebook source
# MAGIC %md
# MAGIC # 03 · Gold — business-ready tables
# MAGIC Gold tables answer the client's questions directly and feed Power BI and the AI assistant.
# MAGIC They store **additive** numbers only (revenue, counts); ratios such as leakage % are calculated
# MAGIC in Power BI so they stay correct at any level of aggregation.

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("schema", "retail")
catalog, schema = dbutils.widgets.get("catalog"), dbutils.widgets.get("schema")

import os, sys
from datetime import timedelta
sys.path.append(os.path.abspath(".."))
from retail import transforms as t
from retail.tables import save

silver = spark.table(f"{catalog}.{schema}.silver_transactions")
as_of = str(silver.agg({"invoice_date": "max"}).first()[0] + timedelta(days=1))
fq = lambda name: f"{catalog}.{schema}.{name}"

# COMMAND ----------

save(t.monthly_kpis(silver), fq("gold_monthly_kpis"),
     "Monthly KPIs by country: gross_revenue (GBP), cancelled_value (GBP), net_revenue, orders, customers, units")
save(t.product_performance(silver), fq("gold_product_performance"),
     "Lifetime performance per product (stock_code): units_sold, gross_revenue, cancelled_value, orders")
save(t.rfm_segments(t.customer_features(silver, as_of)), fq("gold_customer_rfm"),
     f"One row per customer as of {as_of}: recency_days, frequency, monetary (GBP), revenue_365d, RFM scores 1-5, segment")

# COMMAND ----------

display(spark.sql(f"""
  SELECT segment, COUNT(*) AS customers, ROUND(SUM(revenue_365d)) AS revenue_365d
  FROM {fq('gold_customer_rfm')} GROUP BY segment ORDER BY revenue_365d DESC
"""))
