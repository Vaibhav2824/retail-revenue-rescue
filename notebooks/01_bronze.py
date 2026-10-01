# Databricks notebook source
# MAGIC %md
# MAGIC # 01 · Bronze — land the raw extract
# MAGIC Bronze keeps the source **exactly as received** (all strings) plus audit columns, so any later
# MAGIC cleaning decision can be replayed or challenged.

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("schema", "retail")
catalog, schema = dbutils.widgets.get("catalog"), dbutils.widgets.get("schema")

import os, sys
sys.path.append(os.path.abspath(".."))  # repo root, so `retail` is importable from a Git folder
from pyspark.sql import functions as F
from retail.tables import save

# COMMAND ----------

bronze = (
    spark.read.parquet(f"/Volumes/{catalog}/{schema}/raw/")
    .withColumn("_source_file", F.col("_metadata.file_path"))
    .withColumn("_ingested_at", F.current_timestamp())
)
save(bronze, f"{catalog}.{schema}.bronze_transactions", "Raw UCI Online Retail II lines, as received (strings) + audit columns")
display(spark.table(f"{catalog}.{schema}.bronze_transactions").limit(10))
