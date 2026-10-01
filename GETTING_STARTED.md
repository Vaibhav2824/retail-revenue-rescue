# Getting started: your 1-day plan

Everything is already built and tested locally. Your job today is to **run it on Databricks, build the dashboard, record the demo, and be able to explain every part**. Each ✅ checkpoint is something an interviewer may ask, so say the answer out loud.

| Block | Time | Output |
|---|---|---|
| 1. GitHub | 5 min | Repo live, CI green |
| 2. Databricks pipeline | 1.5 h | Tables, lineage, MLflow run |
| 3. Power BI | 2 h | `.pbix` + 3 screenshots |
| 4. Assistant | 45 min | Working app + `eval_results.md` |
| 5. Deck + demo video | 1.5 h | Video link in README |
| 6. Interview prep | 1 h | Pitch + answers |

---

## 1. GitHub (5 min, already pushed)
The repo is at **https://github.com/Vaibhav2824/retail-revenue-rescue**.
1. Turn on CI (one-time, about 1 minute). GitHub needs extra permission to accept workflow files:
   ```bash
   gh auth refresh -h github.com -s workflow
   git add .github && git commit -m "ci: run tests on push" && git push
   ```
   Then check the **Actions** tab: the `tests` workflow should go green within about 3 minutes.
2. On the repo page, click ⚙ next to **About** → add a one-line description and topics (`databricks`, `power-bi`, `mlflow`, `langchain`, `data-engineering`).
3. After each block below: `git add -A && git commit -m "..." && git push`.

## 2. Databricks pipeline (1.5 h)
**a. Bring the code in**
Databricks → **Workspace** → your user folder → **Create → Git folder** → paste the repo URL → Create.

**b. Setup + data**
1. Open `notebooks/00_setup` → top right **Connect → Serverless** → **Run all**.
2. **Catalog** (left bar) → `workspace` → `retail` → **Volumes** → `raw` → **Upload to this volume** → choose `data/online_retail_ii.parquet` from your PC.

**c. Create the job** (this is the "orchestration" the JD mentions)
**Jobs & Pipelines → Create → Job**, then add 4 tasks. Each one is: Type *Notebook*, Source *Workspace*, Path = the notebook in your Git folder, Compute *Serverless*:

| Task name | Notebook | Depends on |
|---|---|---|
| bronze | `notebooks/01_bronze` | none |
| silver | `notebooks/02_silver` | bronze |
| gold | `notebooks/03_gold` | silver |
| churn_model | `notebooks/04_churn_model` | gold |

Name the job `retail-revenue-rescue-pipeline` → **Run now**. It takes about 5–10 minutes. Watch the task graph turn green.

**d. Explore what you built**
- Catalog → `gold_customer_churn_risk` → **Lineage** tab → **See lineage graph**. Take a screenshot (`docs/img/lineage.png`).
- **Experiments** (left bar) → `retail-churn` → open the run → metrics `auc` and `baseline_recency_auc`.
- Open `silver_quarantine` → **Sample data**. These are the rows we excluded, each with a reason.

> ✅ **Checkpoints**
> - *What is bronze/silver/gold?* Bronze is the source as received (replayable). Silver is cleaned, typed and deduplicated. Gold is shaped for business questions.
> - *What does Unity Catalog give you?* One place for permissions, table/column documentation and automatic lineage from source file to dashboard table.
> - *Why does the job fail if retention < 90%?* So a broken extract stops the pipeline instead of silently publishing wrong numbers.
> - *Why out-of-time validation?* A random split lets the model learn from the future. Testing on a later period mirrors how it will actually be used.

**If something fails:** read the error in the task's output, then see [`docs/runbook.md`](docs/runbook.md). The most likely issue: `ModuleNotFoundError: retail`. That means the notebook isn't running from inside the Git folder, so open it from the Git folder path.

## 3. Power BI (2 h)
Follow [`powerbi/BUILD_GUIDE.md`](powerbi/BUILD_GUIDE.md). Save `powerbi/retail_revenue_rescue.pbix` and the three screenshots into `docs/img/`.

## 4. Assistant (45 min)
1. Get a free API key at **console.groq.com → API Keys**.
2. Run:
   ```bash
   py -3.11 -m venv .venv && .venv\Scripts\activate
   pip install -r requirements.txt
   copy .env.example .env      # then paste your key into .env
   streamlit run assistant/app.py
   ```
3. Try the example buttons. Then try something malicious like *"delete all customers"* and watch it get blocked.
4. `python -m assistant.eval` → writes `assistant/eval_results.md`. Commit it, and put the accuracy into your CV bullet.
   - If Groq says the model is decommissioned, set `GROQ_MODEL` in `.env` to a current model from console.groq.com/docs/models.
5. *(Optional, impressive)* Point it at Databricks instead of local files. Fill the `DATABRICKS_*` values in `.env` (same hostname, path and token as in the Power BI guide) and restart.

> ✅ **Checkpoints**
> - *Why show the SQL?* So a business user, or an auditor, can verify the answer. A black-box answer isn't trustworthy for finance numbers.
> - *Is the regex guard enough?* No. It's one layer. In production the connection would use a credential that can only `SELECT` from gold.
> - *Why an eval set?* "It seemed to work" isn't evidence. 10 questions with known answers give a score you can track when you change the prompt or model.

## 5. Deck + demo video (1.5 h)
**Deck:** review `deck/`, then edit the wording until it sounds like you.

**Video (3 min).** Record with Windows **Win + Alt + R** (Game Bar) or Loom free. Upload as **unlisted** YouTube and paste the link at the top of the README.

| Time | Show | Say (roughly) |
|---|---|---|
| 0:00 | README top | "A retailer asked where revenue is leaking and who's about to churn. I treated it like a client engagement." |
| 0:20 | Databricks job graph + lineage | "Four-step pipeline on Databricks: bronze, silver, gold, model. Unity Catalog tracks lineage. Bad rows are quarantined with a reason, never deleted." |
| 0:55 | Power BI page 2 | "Leakage looked like it doubled in 2011. Drilling in, a third of it was two keying errors reversed within minutes. Underlying leakage was flat. So the fix is a cheap order-entry check, not an investigation." |
| 1:40 | Power BI page 3 | "The churn model beats the rule they already use: AUC 0.76 vs 0.71 on a later period it never saw. £1.27M is at risk, and 100 customers hold £203k of it. This is the call list." |
| 2:15 | Assistant | Ask one question, open "SQL used", then show a blocked query. "Managers can self-serve, and every answer shows its SQL." |
| 2:45 | Deck last slide | "Recommendation, the £ scenario, and next phase: add margin data and A/B-test the retention calls." |

## 6. Interview prep (1 h)
**60-second pitch:** problem → one surprising finding → what you built → the result. Practise until it doesn't sound read.

**Likely questions** (answers are in the README "Decisions" section and the ADR):
1. Why Databricks and not AWS Glue or Azure Data Factory?
2. Walk me through how a bad row moves through your pipeline.
3. How do you know your model is better than doing nothing?
4. What would you change if data arrived every hour instead of once?
   *(Auto Loader / incremental MERGE instead of overwrite. Schedule the job. Alert on the quality gate.)*
5. How would you explain revenue at risk to a CFO?
   *(Expected loss: probability × last year's spend, summed. Like a risk-weighted pipeline in sales.)*
6. What's the weakest part of this project?
   *(Honest answer: no cost data, so it's revenue not margin. The retention uplift is an assumption until A/B tested. Regex guard alone wouldn't be enough in production.)*

**CV bullets** (fill in your eval score):
- Built an end-to-end Databricks lakehouse (Unity Catalog, medallion architecture, Workflows) over 1.07M retail transactions, with a data-quality gate and quarantine; PySpark transforms unit-tested in CI.
- Found that 34% of cancellation value came from two order-entry errors, reframing an apparent 2× rise in revenue leakage as flat, and recommended a zero-cost order-entry control.
- Developed an MLflow-tracked churn model validated out-of-time (AUC 0.76 vs 0.71 for the existing business rule), quantifying £1.27M revenue at risk and a 100-customer call list holding £203k.
- Shipped a LangChain text-to-SQL assistant over governed tables with a read-only guard, scoring __% on a 10-question evaluation set; built a 3-page Power BI dashboard with DAX.
