"""Faithfulness + citation-verification for RAG answers.

Run:
    venv\Scripts\python eval\faithfulness_eval.py
"""

import json
import re
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent
sys_path_fix = str(ROOT)
import sys
if sys_path_fix not in sys.path:
    sys.path.insert(0, sys_path_fix)

from lib.rag import retrieve, answer_with_rag


# ---------------------------------------------------------------
# Faithfulness checks
# ---------------------------------------------------------------
_CITATION_RE = re.compile(r"\[(\d+)\]")


def _parse_citations(answer: str) -> list[int]:
    return [int(m) for m in _CITATION_RE.findall(answer)]


def faithfulness_report(question: str) -> dict:
    chunks = retrieve(question, k=6)
    if chunks is None:
        return {
            "question": question,
            "status": "no_evidence",
            "faithfulness": 0.0,
            "citation_coverage": 0.0,
            "unsupported_claims": 1.0,
        }

    evidence_texts = [c.get("text", "") for c in chunks]
    evidence_combined = " ".join(evidence_texts).lower()

    result = answer_with_rag(question)
    if not result:
        return {
            "question": question,
            "status": "no_answer",
            "faithfulness": 0.0,
            "citation_coverage": 0.0,
            "unsupported_claims": 1.0,
        }

    answer = result.get("answer", "")
    citations = result.get("citations", [])
    if not answer:
        return {
            "question": question,
            "status": "empty_answer",
            "faithfulness": 0.0,
            "citation_coverage": 0.0,
            "unsupported_claims": 1.0,
        }

    cited_numbers = set(_parse_citations(answer))
    supported = 0
    unsupported = 0
    for num in cited_numbers:
        idx = num - 1
        if 0 <= idx < len(evidence_texts):
            snippet = evidence_texts[idx].lower()
            # Heuristic: check whether any phrase from the snippet appears in the answer
            words = [w for w in snippet.split() if len(w) > 5][:8]
            if words and any(w in answer.lower() for w in words):
                supported += 1
            else:
                unsupported += 1
        else:
            unsupported += 1

    total_cited = max(len(cited_numbers), 1)
    citation_coverage = supported / total_cited
    # Unsupported ratio is zero if no citations were used at all
    unsupported_ratio = (unsupported / total_cited) if cited_numbers else 0.0
    # Simple faithfulness proxy: coverage minus penalty for unsupported claims
    faithfulness = max(0.0, citation_coverage - unsupported_ratio * 0.5)

    return {
        "question": question,
        "status": "ok",
        "faithfulness": round(faithfulness, 3),
        "citation_coverage": round(citation_coverage, 3),
        "unsupported_claims": round(unsupported_ratio, 3),
        "cited_numbers": sorted(cited_numbers),
        "citations_available": len(citations),
    }


def main():
    queries = [
        "first-line pharmacotherapy for type 2 diabetes",
        "GLP-1 receptor agonist cardiovascular benefit",
        "SGLT2 inhibitor heart failure hospitalization prevention",
        "continuous glucose monitoring type 1 diabetes standard of care",
        "metformin eGFR threshold contraindication",
        "insulin initiation criteria severe hyperglycemia",
    ]
    reports = [faithfulness_report(q) for q in queries]
    for r in reports:
        print(
            f"- {r['question']}\n"
            f"  status={r['status']} faithfulness={r['faithfulness']} "
            f"coverage={r['citation_coverage']} unsupported={r['unsupported_claims']}\n"
        )

    summary = {
        "queries": len(reports),
        "mean_faithfulness": round(sum(r["faithfulness"] for r in reports) / len(reports), 3),
        "mean_citation_coverage": round(
            sum(r["citation_coverage"] for r in reports) / len(reports), 3
        ),
        "mean_unsupported_claims": round(
            sum(r["unsupported_claims"] for r in reports) / len(reports), 3
        ),
        "reports": reports,
    }
    Path("eval").mkdir(exist_ok=True)
    Path("eval/faithfulness_metrics.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print("Saved eval/faithfulness_metrics.json")


if __name__ == "__main__":
    main()
