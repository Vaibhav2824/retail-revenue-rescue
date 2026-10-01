"""Unity Catalog write helper used by the notebooks."""
from pyspark.sql import DataFrame


def save(df: DataFrame, fqn: str, comment: str) -> None:
    """Overwrite a managed Delta table and document it, so the catalog (and the AI assistant) can read what it means."""
    df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(fqn)
    df.sparkSession.sql(f"COMMENT ON TABLE {fqn} IS '{comment}'")
