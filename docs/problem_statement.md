# Engagement brief: UK online gift retailer

*Fictional client, real data (UCI Online Retail II: 1.07M invoice lines, Dec 2009 – Dec 2011, ~5.9k customers, 40+ countries).*

## The client's words
> "Revenue looks fine on the top line, but the finance team says cancellations are eating into it, and our
> account managers only notice a wholesale customer has gone quiet months after they've left.
> We need to know where the money is leaking and who to call before they go."

## Questions we committed to answer
1. **Leakage:** How much gross revenue is lost to cancellations, and which products and months drive it?
2. **Retention:** Which active customers are likely to stop ordering in the next 90 days?
3. **Value:** How much revenue is at risk, so the retention budget can be sized against it?
4. **Self-service:** Can managers get answers without waiting for an analyst?

## Success criteria (agreed up front)
| # | Criterion | How we measure it |
|---|---|---|
| 1 | Every excluded row is explainable | Quarantine table with a reason per row; data-quality gate fails the job if retention < 90% |
| 2 | Churn model beats the rule already in use ("longest since last order") | Out-of-time AUC vs recency-only AUC |
| 3 | Revenue at risk is quantified in £ and broken down to a call list | `gold_customer_churn_risk`, Power BI page 3 |
| 4 | Assistant answers are verifiable | Shows its SQL; ≥ 80% on a 10-question reference eval; read-only guard |
| 5 | Pipeline re-runnable by someone else | One Databricks job, runbook, CI tests |

## Out of scope (and why)
- **Real-time scoring:** the client reviews accounts weekly, so batch is enough.
- **Price elasticity / promotions:** the source has no promotion or cost data.
- **Profit margin:** no cost of goods in the data, so all figures are revenue.
