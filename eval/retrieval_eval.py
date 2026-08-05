"""Retrieval evaluation for the local RAG corpus.

Metrics (single-query form):
- recall@k
- MRR
- nDCG@k

Run:
    venv\Scripts\python eval\retrieval_eval.py
"""

import json
import statistics
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
sys_path_fix = str(ROOT)
import sys
if sys_path_fix not in sys.path:
    sys.path.insert(0, sys_path_fix)

from lib.rag import retrieve, _get_collection

# ---------------------------------------------------------------
# Gold sets: question -> expected source strings (substring match)
# ---------------------------------------------------------------
TEST_SET = [
    {
        "query": "first-line pharmacotherapy for type 2 diabetes",
        "expected_sources": ["ADA_Standards_2026_Ch9_Pharmacologic_Approaches.md"],
    },
    {
        "query": "GLP-1 receptor agonist cardiovascular benefit",
        "expected_sources": ["ADA_Standards_2026_Ch9_Pharmacologic_Approaches.md"],
    },
    {
        "query": "SGLT2 inhibitor heart failure hospitalization prevention",
        "expected_sources": ["ADA_Standards_2026_Ch9_Pharmacologic_Approaches.md"],
    },
    {
        "query": "continuous glucose monitoring type 1 diabetes standard of care",
        "expected_sources": ["ADA_Standards_2026_Ch9_Pharmacologic_Approaches.md"],
    },
    {
        "query": "metformin eGFR threshold contraindication",
        "expected_sources": ["ADA_Standards_2026_Ch9_Pharmacologic_Approaches.md"],
    },
    {
        "query": "insulin initiation criteria severe hyperglycemia",
        "expected_sources": ["ADA_Standards_2026_Ch9_Pharmacologic_Approaches.md"],
    },
    {
        "query": "dual GIP GLP-1 receptor agonist heart failure preserved ejection fraction",
        "expected_sources": ["ADA_Standards_2026_Ch9_Pharmacologic_Approaches.md"],
    },
    {
        "query": "chronic kidney disease diabetes preferred glucose lowering medication",
        "expected_sources": ["ADA_Standards_2026_Ch9_Pharmacologic_Approaches.md"],
    },
]


def _hit_at_k(results: Optional[list[dict]], expected: list[str], k: int) -> bool:
    if not results:
        return False
    for r in results[:k]:
        src = r.get("source", "")
        if any(e in src for e in expected):
            return True
    return False


def _mrr(results: Optional[list[dict]], expected: list[str]) -> float:
    if not results:
        return 0.0
    for idx, r in enumerate(results, start=1):
        src = r.get("source", "")
        if any(e in src for e in expected):
            return 1.0 / idx
    return 0.0


def _ndcg_at_k(results: Optional[list[dict]], expected: list[str], k: int) -> float:
    if not results:
        return 0.0
    relevance = [1.0 if any(e in r.get("source", "") for e in expected) else 0.0 for r in results[:k]]
    dcg = sum(rel / (i + 1) for i, rel in enumerate(relevance))
    ideal_relevance = sorted(relevance, reverse=True)
    idcg = sum(rel / (i + 1) for i, rel in enumerate(ideal_relevance))
    if idcg == 0:
        return 0.0
    return dcg / idcg


def main():
    col = _get_collection()
    total_chunks = col.count()
    print(f"Corpus size: {total_chunks} chunks\n")

    ks = [1, 3, 5, 10]
    rows = []

    for item in TEST_SET:
        res = retrieve(item["query"], k=max(ks))
        hit = {k: _hit_at_k(res, item["expected_sources"], k) for k in ks}
        rows.append({
            "query": item["query"],
            "hits": hit,
            "mrr": _mrr(res, item["expected_sources"]),
            "ndcg@5": _ndcg_at_k(res, item["expected_sources"], 5),
            "top_sources": [r.get("source", "") for r in (res or [])[:3]],
            "top_scores": [round(r.get("score", 0.0), 3) for r in (res or [])[:3]],
        })

    print(f"{'Query':<65} {'R@1':>5} {'R@3':>5} {'R@5':>5} {'MRR':>6} {'nDCG@5':>7}")
    print("-" * 95)
    recall_sums = {k: 0 for k in ks}
    mrr_vals = []
    ndcg_vals = []
    for row in rows:
        r1 = row["hits"][1]
        r3 = row["hits"][3]
        r5 = row["hits"][5]
        recall_sums[1] += int(r1)
        recall_sums[3] += int(r3)
        recall_sums[5] += int(r5)
        mrr_vals.append(row["mrr"])
        ndcg_vals.append(row["ndcg@5"])
        print(
            f"{row['query']:<65} {int(r1):>5} {int(r3):>5} {int(r5):>5} "
            f"{row['mrr']:>6.3f} {row['ndcg@5']:>7.3f}"
        )
    print("-" * 95)
    n = len(rows)
    print(
        f"{'mean':<65} "
        f"{recall_sums[1]/n:>5.2f} {recall_sums[3]/n:>5.2f} {recall_sums[5]/n:>5.2f} "
        f"{statistics.mean(mrr_vals):>6.3f} {statistics.mean(ndcg_vals):>7.3f}"
    )

    print("\n--- Top retrieval samples ---")
    for row in rows[:3]:
        print("Q:", row["query"])
        for s, sc in zip(row["top_sources"], row["top_scores"]):
            print(" ", sc, "|", s)
        print()

    out = {
        "corpus_size": total_chunks,
        "queries": len(rows),
        "recall@1": recall_sums[1] / n,
        "recall@3": recall_sums[3] / n,
        "recall@5": recall_sums[5] / n,
        "mrr": statistics.mean(mrr_vals),
        "ndcg@5": statistics.mean(ndcg_vals),
        "rows": rows,
    }
    Path("eval").mkdir(exist_ok=True)
    Path("eval/retrieval_metrics.json").write_text(
        json.dumps(out, indent=2), encoding="utf-8"
    )
    print("Saved eval/retrieval_metrics.json")


if __name__ == "__main__":
    main()
