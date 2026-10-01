# Power BI dashboard: build guide (about 2 hours, first-timer friendly)

Save your work as `powerbi/retail_revenue_rescue.pbix` and commit it.

## 1. Get the data (pick ONE route)

**Route A: live from Databricks** (shows the end-to-end story; use this if it works)
1. Databricks → **SQL Warehouses** → *Serverless Starter Warehouse* → **Connection details**. Copy *Server hostname* and *HTTP path*.
2. Databricks → your profile (top right) → **Settings → Developer → Access tokens → Generate new token** (lifetime 30 days).
3. Power BI Desktop → **Get data → More… → search "Databricks"** → choose **Databricks** (not *Azure* Databricks: Free Edition runs on AWS).
4. Paste the hostname and HTTP path. Data connectivity mode: **Import**. Auth: **Personal Access Token**.
5. Navigator → `workspace` → `retail` → tick the 4 `gold_*` tables → **Load**.

**Route B: offline** (fallback if the connector or token gives trouble)
**Get data → Parquet** → load each file in `data/gold/` (use the full local path). The tables are identical.

> ✅ **Checkpoint:** in Model view you should see 4 tables. Why *Import* and not *DirectQuery*? The data is small, and Import keeps the dashboard fast even when the free warehouse is asleep.

## 2. Model

1. **Home → New table**, paste:
   ```DAX
   Calendar = ADDCOLUMNS(CALENDAR(DATE(2009,12,1), DATE(2011,12,31)), "Year", YEAR([Date]), "Month", FORMAT([Date], "MMM yyyy"), "MonthNo", YEAR([Date])*100 + MONTH([Date]))
   ```
   Select it → **Table tools → Mark as date table** → `Date`. Select the `Month` column → **Sort by column** → `MonthNo`.
2. **Model view:** drag `Calendar[Date]` onto `gold_monthly_kpis[month]` (one-to-many).
3. Select `gold_monthly_kpis` → **New measure** for each line in [`measures.dax`](measures.dax). Format the £ measures as Currency (£ English UK) and the % measures as Percentage.

> ✅ **Checkpoint:** explain why `Leakage %` is `DIVIDE(SUM(cancelled), SUM(gross))` and not an average of monthly percentages. (Answer: an average of ratios overweights small months. Ratio of sums is correct at every level.)

## 3. Pages

Use one colour for "good" (net revenue) and one accent for "risk" (leakage, churn) across every page.

**Page 1: Executive overview**
- 4 **Cards**: `Net Revenue`, `Leakage %`, `Revenue at Risk`, `Active Customers`
- **Line chart**: X `Calendar[Month]`, Y `Net Revenue`, secondary Y `Leakage %`
- **Bar chart**: `gold_monthly_kpis[country]` by `Net Revenue`, top 10 (Filters pane → Top N)
- **Slicer**: `Calendar[Year]`
- Title text box with the headline finding (copy it from the deck)

**Page 2: Revenue leakage**
- **Line chart**: `Calendar[Month]` by `Leakage %`
- **Bar chart**: `gold_product_performance[description]` by `Product Cancelled Value`, Top N = 10
- **Table**: description, `Product Gross Revenue`, `Product Cancelled Value`, `Product Cancel Rate`. Visual-level filter: `Product Gross Revenue` > 1000, sorted by cancel rate descending

**Page 3: Churn risk (the action list)**
- **Cards**: `Revenue at Risk`, `High-Risk Customers`, `Revenue at Risk (High-Risk)`
- **Bar chart**: `gold_customer_rfm[segment]` by `Customers in Segment`
- **Scatter**: X `recency_days`, Y `revenue_365d`, Values `customer_id`, Legend: none, colour saturation `churn_probability` (from `gold_customer_churn_risk`)
- **Table**: customer_id, country, revenue_365d, churn_probability, revenue_at_risk. Sort by revenue_at_risk descending, Top N = 25. Title it **"Call list for the retention team"**

> ✅ **Checkpoint:** say in one sentence what the retention team should do on Monday morning using page 3.

## 4. Finish
- **View → Themes → Browse for themes** → `powerbi/theme.json` (matches the deck colours).
- Screenshot each page into `docs/img/` (`overview.png`, `leakage.png`, `churn.png`). The README links to them.
