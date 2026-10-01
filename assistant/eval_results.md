# Assistant eval: 100% (10/10)

| Question | Result | Generated SQL |
|---|---|---|
| What was total net revenue in 2011? | ✅ | `SELECT ROUND(SUM(net_revenue), 2) AS total_net_revenue_2011 FROM gold_monthly_kpis WHERE month >= DATE '2011-01-01' AND month < DATE '2012-01-01' LIMIT 200` |
| Which 5 countries outside the United Kingdom had the highest gross revenue? | ✅ | `SELECT country, ROUND(SUM(gross_revenue), 2) AS total_gross_revenue_gbp FROM gold_monthly_kpis WHERE country <> 'United Kingdom' GROUP BY country ORDER BY total_gross_revenue_gbp DESC LIMIT 5` |
| What percentage of gross revenue was lost to cancellations over the whole period? | ✅ | `SELECT ROUND((SUM(cancelled_value) / NULLIF(SUM(gross_revenue), 0)) * 100, 2) AS cancellation_loss_pct FROM gold_monthly_kpis LIMIT 200` |
| Which single month had the highest net revenue across all countries? | ✅ | `SELECT month, ROUND(SUM(net_revenue), 2) AS total_net_revenue_gbp FROM gold_monthly_kpis GROUP BY month ORDER BY total_net_revenue_gbp DESC LIMIT 1` |
| How many customers are in each RFM segment? | ✅ | `SELECT segment AS rfm_segment, COUNT(*) AS customer_count FROM gold_customer_rfm GROUP BY segment ORDER BY segment LIMIT 200` |
| What is the total revenue at risk from customer churn? | ✅ | `SELECT ROUND(SUM(revenue_at_risk), 2) AS total_revenue_at_risk_gbp FROM gold_customer_churn_risk LIMIT 200` |
| List the 10 customers with the highest revenue at risk. | ✅ | `SELECT customer_id, country, ROUND(churn_probability, 2) AS churn_probability, ROUND(revenue_at_risk, 2) AS revenue_at_risk FROM gold_customer_churn_risk ORDER BY revenue_at_risk DESC LIMIT 10` |
| Which 5 products lost the most money to cancellations? | ✅ | `SELECT stock_code, description, ROUND(cancelled_value, 2) AS cancelled_value_gbp FROM gold_product_performance ORDER BY cancelled_value DESC LIMIT 5` |
| How many active customers have a churn probability above 50%? | ✅ | `SELECT COUNT(*) AS active_customers_high_churn FROM gold_customer_churn_risk WHERE churn_probability > 0.5 LIMIT 200` |
| Which country has the most customers in the At Risk segment? | ✅ | `SELECT country, COUNT(*) AS at_risk_customer_count FROM gold_customer_rfm WHERE segment = 'At Risk' GROUP BY country ORDER BY at_risk_customer_count DESC LIMIT 1` |
