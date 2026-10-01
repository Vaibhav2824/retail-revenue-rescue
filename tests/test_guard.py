import pytest

from assistant.core import ROW_LIMIT, UnsafeSQL, guard


@pytest.mark.parametrize("sql", [
    "DROP TABLE gold_customer_rfm",
    "SELECT 1; DROP TABLE gold_customer_rfm",
    "DELETE FROM gold_monthly_kpis",
    "WITH x AS (SELECT 1) INSERT INTO t SELECT * FROM x",
    "SELECT * FROM read_parquet('C:/secrets.parquet')",
    "SELECT 1 -- ; drop table x",
    "SELECT 1 /* hidden */",
    "UPDATE gold_customer_rfm SET segment = 'x'",
    "",
])
def test_blocks_anything_that_is_not_a_single_read(sql):
    with pytest.raises(UnsafeSQL):
        guard(sql)


def test_allows_keywords_inside_string_literals():
    sql = "SELECT * FROM gold_product_performance WHERE description LIKE '%SET OF 5%'"
    assert guard(sql).startswith(sql)


def test_strips_markdown_fences_and_trailing_semicolon():
    assert guard("```sql\nSELECT 1;\n```") == f"SELECT 1\nLIMIT {ROW_LIMIT}"


def test_caps_large_limits_but_keeps_small_ones():
    assert guard("SELECT 1 LIMIT 10") == "SELECT 1 LIMIT 10"
    assert guard("SELECT 1 LIMIT 100000") == f"SELECT 1 LIMIT {ROW_LIMIT}"
