"""Score the assistant: does its SQL return the same answer as a hand-written reference query?

    python -m assistant.eval        (needs GROQ_API_KEY; writes assistant/eval_results.md)
Column names may differ; every reference column must match some returned column (numbers within 0.5%).
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from assistant.core import query, run_sql

HERE = Path(__file__).parent


def _norm(s: pd.Series) -> list:
    if pd.api.types.is_numeric_dtype(s):
        return sorted(s.astype(float).round(2).tolist())
    return sorted(str(v.isoformat()[:10] if hasattr(v, "isoformat") else v) for v in s)


def results_match(ref: pd.DataFrame, got: pd.DataFrame) -> bool:
    if len(ref) != len(got):
        return False
    got_cols = [_norm(got[c]) for c in got.columns]
    for c in ref.columns:
        want = _norm(ref[c])
        if not any(
            g == want or (len(g) == len(want) and all(isinstance(x, float) for x in g + want)
                          and np.allclose(g, want, rtol=0.005))
            for g in got_cols
        ):
            return False
    return True


def main() -> None:
    cases = json.loads((HERE / "eval_set.json").read_text())
    rows = []
    for case in cases:
        try:
            sql, got = query(case["question"])
            ok = results_match(run_sql(case["sql"]), got)
        except Exception as exc:
            sql, ok = f"ERROR: {exc}", False
        rows.append((case["question"], ok, sql))
        print(("PASS " if ok else "FAIL ") + case["question"])

    score = sum(ok for _, ok, _ in rows) / len(rows)
    lines = [f"# Assistant eval: {score:.0%} ({sum(ok for _, ok, _ in rows)}/{len(rows)})", "",
             "| Question | Result | Generated SQL |", "|---|---|---|"]
    lines += [f"| {q} | {'✅' if ok else '❌'} | `{' '.join(s.split())}` |" for q, ok, s in rows]
    (HERE / "eval_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nAccuracy: {score:.0%}")


if __name__ == "__main__":
    main()
