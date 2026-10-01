# ADR-001: Platform and tool choices

**Status:** accepted · **Context:** a mid-size retailer with no existing data platform, a small analytics team,
weekly decision cadence, about 1M rows/year growing. Must be explainable to a non-technical sponsor.

## Decision
| Need | Chosen | Considered | Why chosen |
|---|---|---|---|
| Processing + storage | **Databricks (Delta, medallion)** | AWS Glue + S3 + Athena; Azure Data Factory + Synapse | One platform for ETL, ML and SQL serving. Glue/ADF would need 3–4 services stitched together for the same result. Same Spark code scales if volume grows 100×. |
| Governance | **Unity Catalog** | Glue Data Catalog; Purview | Table/column comments, lineage and permissions in the same place the data lives. The AI assistant reuses those descriptions. |
| Orchestration | **Databricks Workflows** (bundle in `databricks.yml`) | ADF pipelines; Airflow | 4 sequential notebook tasks don't justify a separate orchestrator. ADF becomes the right call if many non-Databricks sources must be landed. |
| ML tracking | **MLflow** | Azure ML; SageMaker | Built into the platform. Every score in gold carries the `model_run_id` that produced it. |
| Model | **Gradient-boosted trees (scikit-learn)** | Logistic regression; deep learning | Handles skewed spend data without manual transforms. ~3k training rows doesn't need distributed ML or deep learning. |
| BI | **Power BI** | Tableau; Databricks AI/BI dashboards | Most common at UK enterprise clients and familiar to the sponsor's team. Tableau would be equally valid if the client already licensed it. |
| GenAI | **LangChain + Groq-hosted gpt-oss-120b** | Azure OpenAI; Databricks Genie | Provider-agnostic: swapping to Azure OpenAI is a one-line change in `assistant/core.py` (`_llm()`). Free tier for the proof of concept. |

## Consequences
- **Vendor lock-in is limited:** the transforms are plain PySpark functions (tested locally without Databricks), and the gold tables are Delta/Parquet that any engine can read.
- **Cost:** serverless compute is billed per use. For weekly runs at this size the cost is small. Re-evaluate if the data grows to hourly loads.
- **Risk:** text-to-SQL can be wrong. Mitigated by showing the SQL, a reference eval, and a read-only guard plus a read-only credential.
