# Runbook: operating the pipeline

## Normal run
Databricks → **Jobs & Pipelines** → `retail-revenue-rescue-pipeline` → **Run now**. Tasks: bronze → silver → gold → churn_model (~5–10 min on serverless).

New source extract? Upload it to `/Volumes/workspace/retail/raw/` and run the job. Bronze reads every file in the volume, so remove superseded extracts first.

## When something fails
| Symptom | Likely cause | Fix |
|---|---|---|
| `silver` fails with *Data-quality gate failed* | Source format changed (new columns, different date format) and most rows became `unparseable` | Query `silver_quarantine` grouped by `reject_reason`. Fix the extract or update `retail/transforms.py:label_rows`, add a test, rerun. |
| `bronze` fails with *path does not exist* | Volume empty or wrong catalog/schema | Check job parameters `catalog` / `schema`. Upload the file. |
| `churn_model` fails at `%pip install` | Transient PyPI/network issue | Repair run (reruns only the failed task). |
| `churn_model` AUC drops below the recency baseline | Behaviour shift (e.g. a seasonal peak) | Do **not** publish scores. Check the MLflow run comparison. Retrain with a longer training window. |
| Power BI refresh fails | Access token expired (30 days) | Generate a new token and update the data source credentials. |
| Assistant says *Blocked by the safety guard* | The model generated non-SELECT SQL | Working as intended. Rephrase the question. |

## Security
- `DATABRICKS_TOKEN` and `GROQ_API_KEY` live only in `.env` (git-ignored).
- For a real client, the assistant would connect with a service principal that has only `SELECT` on `gold_*` tables (`GRANT SELECT ON SCHEMA workspace.retail TO ...`). The SQL guard is a second layer, not the only one.
- Customer IDs are pseudonymous in the source. No names, emails or addresses are stored.
