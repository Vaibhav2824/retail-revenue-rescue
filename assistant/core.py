"""'Ask the data' assistant: question -> SQL (LLM) -> read-only guard -> run on gold tables -> plain-English answer.

Backend: Databricks SQL warehouse if DATABRICKS_SERVER_HOSTNAME is set, otherwise local DuckDB over
data/gold/*.parquet (written by scripts/run_local.py).
"""
import os
import re
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

GOLD_DIR = Path(__file__).resolve().parents[1] / "data" / "gold"
ROW_LIMIT = 200

SCHEMA = """
gold_monthly_kpis(month DATE first day of month, country STRING, gross_revenue DOUBLE GBP of sales,
  cancelled_value DOUBLE GBP of cancelled lines (positive number), net_revenue DOUBLE = gross - cancelled,
  orders BIGINT distinct sale invoices, customers BIGINT distinct buying customers, units BIGINT)
  -- one row per month x country, Dec 2009 to Dec 2011. Leakage % = SUM(cancelled_value) / SUM(gross_revenue).
gold_product_performance(stock_code STRING, description STRING, units_sold BIGINT, gross_revenue DOUBLE,
  cancelled_value DOUBLE, orders BIGINT)  -- one row per product, whole period
gold_customer_rfm(customer_id STRING, country STRING, last_purchase DATE, first_purchase DATE,
  frequency BIGINT orders, monetary DOUBLE lifetime net GBP, revenue_365d DOUBLE net GBP in last 12 months,
  orders_90d BIGINT, distinct_products BIGINT, cancel_rate DOUBLE 0-1, avg_order_value DOUBLE,
  recency_days INT days since last order, tenure_days INT, r_score INT 1-5, f_score INT 1-5, m_score INT 1-5,
  segment STRING one of Champions, Loyal, Promising, Needs Attention, At Risk, Hibernating)
  -- one row per customer, as of 2011-12-10
gold_customer_churn_risk(customer_id STRING, country STRING, same behaviour columns as gold_customer_rfm,
  churn_probability DOUBLE 0-1 chance of no order in next 90 days, revenue_at_risk DOUBLE GBP = churn_probability x revenue_365d)
  -- active customers only (ordered in last 365 days)
"""

SQL_PROMPT = """You are a SQL analyst for a UK online gift retailer. Write ONE SQL SELECT query that answers the question.
Tables (use these exact unqualified names):
{schema}
Rules: SELECT/WITH only. Standard SQL that runs on both Databricks SQL and DuckDB. Round money to 2 decimals.
Give result columns clear names. Return only the SQL, no explanation, no markdown.
{error}
Question: {question}"""

ANSWER_PROMPT = """You are a data consultant. Answer the client's question in 2-3 plain-English sentences using ONLY
the query result below. Quote the key numbers (GBP with £). If the result is empty, say so.
Question: {question}
Result (CSV):
{result}"""

FORBIDDEN = re.compile(
    r"\b(insert|update|delete|merge|drop|create|alter|truncate|grant|revoke|copy|call|exec|execute|attach|"
    r"install|load|pragma|set|use|optimize|vacuum|refresh|read_csv|read_parquet|read_json|read_files)\b",
    re.IGNORECASE,
)


class UnsafeSQL(ValueError):
    pass


def guard(sql: str) -> str:
    """Allow a single read-only query and cap its size. Defence in depth: the warehouse
    credential should ALSO be read-only (see docs/runbook.md)."""
    sql = re.sub(r"^```(?:sql)?|```$", "", sql.strip(), flags=re.IGNORECASE).strip().rstrip(";").strip()
    code = re.sub(r"'(?:[^']|'')*'", "''", sql)  # check keywords outside string literals ('SET OF 5 MUGS' is fine)
    if not code:
        raise UnsafeSQL("empty query")
    if ";" in code or "--" in code or "/*" in code:
        raise UnsafeSQL("multiple statements or comments are not allowed")
    if not re.match(r"^(select|with)\b", code, re.IGNORECASE):
        raise UnsafeSQL("only SELECT queries are allowed")
    if m := FORBIDDEN.search(code):
        raise UnsafeSQL(f"forbidden keyword: {m.group(0)}")
    if m := re.search(r"\blimit\s+(\d+)\s*$", code, re.IGNORECASE):
        return sql if int(m.group(1)) <= ROW_LIMIT else sql[: m.start()] + f"LIMIT {ROW_LIMIT}"
    return f"{sql}\nLIMIT {ROW_LIMIT}"


def run_sql(sql: str) -> pd.DataFrame:
    if os.getenv("DATABRICKS_SERVER_HOSTNAME"):
        from databricks import sql as dbsql

        with dbsql.connect(
            server_hostname=os.environ["DATABRICKS_SERVER_HOSTNAME"],
            http_path=os.environ["DATABRICKS_HTTP_PATH"],
            access_token=os.environ["DATABRICKS_TOKEN"],
            catalog=os.getenv("DATABRICKS_CATALOG", "workspace"),
            schema=os.getenv("DATABRICKS_SCHEMA", "retail"),
        ) as conn, conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall_arrow().to_pandas()

    import duckdb

    with duckdb.connect() as con:
        for f in GOLD_DIR.glob("gold_*.parquet"):
            con.execute(f"CREATE VIEW {f.stem} AS SELECT * FROM read_parquet('{f.as_posix()}')")
        return con.execute(sql).df()


def _llm():
    from langchain_groq import ChatGroq

    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY is not set. Copy .env.example to .env and add your free key from console.groq.com")
    return ChatGroq(model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"), temperature=0)


def generate_sql(question: str, error: str = "") -> str:
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    chain = ChatPromptTemplate.from_template(SQL_PROMPT) | _llm() | StrOutputParser()
    hint = f"Your previous query failed with: {error}\nFix it." if error else ""
    return chain.invoke({"schema": SCHEMA, "question": question, "error": hint})


def query(question: str) -> tuple[str, pd.DataFrame]:
    """Question -> (safe SQL, result). Retries once, feeding the database error back to the model."""
    error = ""
    for _ in range(2):
        sql = generate_sql(question, error)  # outside try: API/key errors should surface, not be retried
        try:
            safe = guard(sql)
            return safe, run_sql(safe)
        except UnsafeSQL:
            raise  # never retry around the safety guard
        except Exception as exc:  # SQL error -> let the model self-correct once
            error = str(exc)[:500]
    raise RuntimeError(f"Could not answer: {error}")


def ask(question: str) -> dict:
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import ChatPromptTemplate

    sql, data = query(question)
    chain = ChatPromptTemplate.from_template(ANSWER_PROMPT) | _llm() | StrOutputParser()
    answer = chain.invoke({"question": question, "result": data.head(30).to_csv(index=False)})
    return {"sql": sql, "data": data, "answer": answer}
