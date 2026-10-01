# Databricks notebook source
# MAGIC %md
# MAGIC # 00 · Setup — catalog objects
# MAGIC Run once. Creates the `retail` schema and a `raw` **volume** (governed file storage in Unity Catalog).
# MAGIC
# MAGIC **After running:** Catalog → `workspace` → `retail` → Volumes → `raw` → **Upload to this volume** → pick `data/online_retail_ii.parquet`.

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("schema", "retail")
catalog, schema = dbutils.widgets.get("catalog"), dbutils.widgets.get("schema")

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema} COMMENT 'Retail Revenue Rescue: medallion tables for the client engagement'")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {catalog}.{schema}.raw COMMENT 'Landing zone for source extracts'")
print(f"Upload the parquet file to /Volumes/{catalog}/{schema}/raw/")
