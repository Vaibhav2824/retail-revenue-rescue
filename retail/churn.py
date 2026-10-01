"""Churn model: train on one snapshot, validate on a LATER snapshot (out-of-time), then score.

Plain pandas + scikit-learn so it runs anywhere; MLflow logging lives in the notebook.
"""
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

FEATURES = [
    "recency_days", "frequency", "monetary", "revenue_365d", "orders_90d",
    "distinct_products", "cancel_rate", "avg_order_value", "tenure_days",
]
PARAMS = {"max_depth": 3, "learning_rate": 0.05, "max_iter": 300, "random_state": 42}


def train(snapshot: pd.DataFrame) -> HistGradientBoostingClassifier:
    return HistGradientBoostingClassifier(**PARAMS).fit(snapshot[FEATURES], snapshot["churned"])


def evaluate(model, snapshot: pd.DataFrame) -> dict[str, float]:
    """Compare against the rule a client already uses: 'longest since last order = most at risk'."""
    y = snapshot["churned"]
    proba = model.predict_proba(snapshot[FEATURES])[:, 1]
    top = snapshot.assign(p=proba).nlargest(max(1, len(snapshot) // 10), "p")
    return {
        "auc": round(roc_auc_score(y, proba), 4),
        "baseline_recency_auc": round(roc_auc_score(y, snapshot["recency_days"]), 4),
        "precision_top_decile": round(top["churned"].mean(), 4),
        "churn_base_rate": round(y.mean(), 4),
        "customers": len(snapshot),
    }


def score(model, features: pd.DataFrame) -> pd.DataFrame:
    """Expected revenue at risk = P(churn) x last-12-month revenue."""
    proba = model.predict_proba(features[FEATURES])[:, 1]
    return features.assign(
        churn_probability=proba.round(4),
        revenue_at_risk=(proba * features["revenue_365d"].clip(lower=0)).round(2),
    )
