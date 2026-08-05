"""Automated eval pipeline runner.

Runs:
- eval/retrieval_eval.py
- eval/faithfulness_eval.py
- eval/redteam_eval.py

Aggregates results into eval/report.json.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "eval"
EVAL_DIR.mkdir(exist_ok=True)

SUITES = [
    ("retrieval", "eval/retrieval_eval.py", "eval/retrieval_metrics.json"),
    # Faithfulness is slower because it calls the LLM backend; run it separately if needed.
    # ("faithfulness", "eval/faithfulness_eval.py", "eval/faithfulness_metrics.json"),
    ("redteam", "eval/redteam_eval.py", "eval/redteam_report.json"),
]

report = {
    "project": "MedAgentic",
    "suites": {},
    "overall": {"passed": 0, "failed": 0, "status": "unknown"},
}

overall_pass = True

for name, script, expected_json in SUITES:
    path = ROOT / script
    if not path.exists():
        report["suites"][name] = {"status": "missing", "error": f"{script} not found"}
        overall_pass = False
        continue

    proc = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=300,
    )
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()

    json_path = ROOT / expected_json
    metrics = None
    if json_path.exists():
        try:
            metrics = json.loads(json_path.read_text(encoding="utf-8"))
        except Exception:
            metrics = None

    suite_pass = proc.returncode == 0
    if not suite_pass:
        overall_pass = False

    report["suites"][name] = {
        "status": "passed" if suite_pass else "failed",
        "returncode": proc.returncode,
        "stdout": stdout,
        "stderr": stderr[-1000:] if stderr else "",
        "metrics": metrics,
    }

report["overall"] = {
    "status": "passed" if overall_pass else "failed",
    "passed": sum(1 for s in report["suites"].values() if s.get("status") == "passed"),
    "failed": sum(1 for s in report["suites"].values() if s.get("status") == "failed"),
}

(EVAL_DIR / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report["overall"], indent=2))
if not overall_pass:
    sys.exit(1)
