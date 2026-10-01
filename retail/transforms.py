"""Bronze -> silver -> gold transformations.

Pure functions (DataFrame in, DataFrame out) so the same code runs in Databricks notebooks
and in local pytest. Writing tables is the notebook's job, not this module's.
"""
from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

PRODUCT_CODE = r"^[0-9]{5}"  # real products; POST, DOT, M, BANK CHARGES etc. are fees/adjustments
ACTIVE_WINDOW_DAYS = 365


# ---------- silver ----------

def label_rows(bronze: DataFrame) -> DataFrame:
    """Type the raw strings and tag every row with a reject_reason (null = clean)."""
    typed = bronze.select(
        F.trim("invoice").alias("invoice"),
        F.upper(F.trim("stock_code")).alias("stock_code"),
        F.trim("description").alias("description"),
        F.expr("try_cast(quantity AS INT)").alias("quantity"),
        F.expr("try_cast(invoice_date AS TIMESTAMP)").alias("invoice_ts"),
        F.expr("try_cast(price AS DOUBLE)").alias("price"),
        F.trim("customer_id").alias("customer_id"),
        F.trim("country").alias("country"),
    ).dropDuplicates()

    is_cancel = F.col("invoice").startswith("C")
    reason = (
        F.when(F.col("invoice_ts").isNull() | F.col("quantity").isNull() | F.col("price").isNull(), "unparseable")
        .when(F.col("invoice").startswith("A"), "bad_debt_adjustment")
        .when(~F.col("stock_code").rlike(PRODUCT_CODE), "non_product_code")
        .when(F.col("price") <= 0, "zero_or_negative_price")
        # sales must be positive and cancellations negative; anything else is a stock write-off
        .when(is_cancel != (F.col("quantity") < 0), "stock_writeoff")
    )
    return typed.withColumn("is_cancellation", is_cancel).withColumn("reject_reason", reason)


def to_silver(labelled: DataFrame) -> DataFrame:
    return (
        labelled.filter(F.col("reject_reason").isNull())
        .drop("reject_reason")
        .withColumn("invoice_date", F.to_date("invoice_ts"))
        .withColumn("line_value", F.round(F.col("quantity") * F.col("price"), 2))
    )


def to_quarantine(labelled: DataFrame) -> DataFrame:
    return labelled.filter(F.col("reject_reason").isNotNull())


# ---------- gold ----------

def _sale(col: str):
    return F.when(~F.col("is_cancellation"), F.col(col))


def _cancel(col: str):
    return F.when(F.col("is_cancellation"), F.col(col))


def monthly_kpis(silver: DataFrame) -> DataFrame:
    """Store additive measures only; ratios like leakage % are computed in Power BI."""
    return (
        silver.groupBy(F.trunc("invoice_date", "month").alias("month"), "country")
        .agg(
            F.round(F.coalesce(F.sum(_sale("line_value")), F.lit(0.0)), 2).alias("gross_revenue"),
            F.round(F.coalesce(-F.sum(_cancel("line_value")), F.lit(0.0)), 2).alias("cancelled_value"),
            F.countDistinct(_sale("invoice")).alias("orders"),
            F.countDistinct(_sale("customer_id")).alias("customers"),
            F.coalesce(F.sum(_sale("quantity")), F.lit(0)).alias("units"),
        )
        .withColumn("net_revenue", F.round(F.col("gross_revenue") - F.col("cancelled_value"), 2))
    )


def product_performance(silver: DataFrame) -> DataFrame:
    return (
        silver.groupBy("stock_code")
        .agg(
            F.max("description").alias("description"),
            F.coalesce(F.sum(_sale("quantity")), F.lit(0)).alias("units_sold"),
            F.round(F.coalesce(F.sum(_sale("line_value")), F.lit(0.0)), 2).alias("gross_revenue"),
            F.round(F.coalesce(-F.sum(_cancel("line_value")), F.lit(0.0)), 2).alias("cancelled_value"),
            F.countDistinct(_sale("invoice")).alias("orders"),
        )
    )


def customer_features(silver: DataFrame, as_of: str) -> DataFrame:
    """Per-customer behaviour using only transactions before `as_of` (no future leakage)."""
    as_of_d = F.to_date(F.lit(as_of))
    past = silver.filter(F.col("customer_id").isNotNull() & (F.col("invoice_date") < as_of_d))
    recent = F.col("invoice_date") >= F.date_sub(as_of_d, ACTIVE_WINDOW_DAYS)
    last_90 = F.col("invoice_date") >= F.date_sub(as_of_d, 90)
    gross = F.coalesce(F.sum(_sale("line_value")), F.lit(0.0))
    return (
        past.groupBy("customer_id")
        .agg(
            F.max("country").alias("country"),
            F.max(_sale("invoice_date")).alias("last_purchase"),
            F.min(_sale("invoice_date")).alias("first_purchase"),
            F.countDistinct(_sale("invoice")).alias("frequency"),
            F.round(F.sum("line_value"), 2).alias("monetary"),
            F.round(F.coalesce(F.sum(F.when(recent, F.col("line_value"))), F.lit(0.0)), 2).alias("revenue_365d"),
            F.countDistinct(F.when(last_90 & ~F.col("is_cancellation"), F.col("invoice"))).alias("orders_90d"),
            F.countDistinct(_sale("stock_code")).alias("distinct_products"),
            F.round(F.try_divide(F.coalesce(-F.sum(_cancel("line_value")), F.lit(0.0)), gross), 4).alias("cancel_rate"),
            F.round(F.try_divide(gross, F.countDistinct(_sale("invoice"))), 2).alias("avg_order_value"),
        )
        .filter(F.col("frequency") > 0)  # customers who only ever cancelled have no behaviour to model
        .withColumn("recency_days", F.datediff(as_of_d, "last_purchase"))
        .withColumn("tenure_days", F.datediff(as_of_d, "first_purchase"))
        .withColumn("as_of", as_of_d)
    )


def rfm_segments(features: DataFrame) -> DataFrame:
    # ponytail: unpartitioned window = single partition; fine for ~6k customers, partition by country at 10M+
    score = lambda col, asc=True: F.ntile(5).over(Window.orderBy(F.col(col).asc() if asc else F.col(col).desc()))
    scored = (
        features.withColumn("r_score", score("recency_days", asc=False))
        .withColumn("f_score", score("frequency"))
        .withColumn("m_score", score("monetary"))
    )
    r, f = F.col("r_score"), F.col("f_score")
    segment = (
        F.when((r >= 4) & (f >= 4), "Champions")
        .when((r >= 4) & (f <= 2), "Promising")
        .when((r >= 3) & (f >= 3), "Loyal")
        .when((r <= 2) & (f >= 3), "At Risk")
        .when(r <= 2, "Hibernating")
        .otherwise("Needs Attention")
    )
    return scored.withColumn("segment", segment)


def churn_snapshot(silver: DataFrame, as_of: str, horizon_days: int = 90) -> DataFrame:
    """Features at `as_of` for customers active in the prior year, labelled churned=1
    if they place no order in the following `horizon_days`."""
    as_of_d = F.to_date(F.lit(as_of))
    returned = (
        silver.filter(
            ~F.col("is_cancellation")
            & F.col("customer_id").isNotNull()
            & (F.col("invoice_date") >= as_of_d)
            & (F.col("invoice_date") < F.date_add(as_of_d, horizon_days))
        )
        .select("customer_id").distinct().withColumn("returned", F.lit(1))
    )
    active = customer_features(silver, as_of).filter(F.col("recency_days") <= ACTIVE_WINDOW_DAYS)
    return (
        active.join(returned, "customer_id", "left")
        .withColumn("churned", F.when(F.col("returned").isNull(), 1).otherwise(0))
        .drop("returned")
    )
