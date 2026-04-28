"""
generate_word_report.py
-----------------------
Standalone script to compile the WEEKLY_SUMMARY_RESULTS.json into a Word document.
NO AI calls — pure JSON → Word mapping. Runs in under 5 seconds.

Usage:
    python generate_word_report.py
    python generate_word_report.py --json path/to/custom.json --out path/to/output.docx
"""

import json
import os
import sys
import argparse

# Ensure backend root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generator import ReportGenerator

# ── Defaults ──────────────────────────────────────────────────────────────────
DEFAULT_JSON   = os.path.join(os.path.dirname(__file__), "tests", "tests_output", "WEEKLY_SUMMARY_RESULTS.json")
DEFAULT_TMPL   = os.path.join(os.path.dirname(__file__), "weekly_template.docx")
DEFAULT_OUTPUT = os.path.join(os.path.dirname(__file__), "tests", "tests_output", "GENERATED_WEEKLY_REPORT.docx")
# ──────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Compile weekly JSON into Word report (no AI).")
    parser.add_argument("--json",     default=DEFAULT_JSON,   help="Path to WEEKLY_SUMMARY_RESULTS.json")
    parser.add_argument("--template", default=DEFAULT_TMPL,   help="Path to weekly_template.docx")
    parser.add_argument("--out",      default=DEFAULT_OUTPUT, help="Output .docx path")
    args = parser.parse_args()

    # Validate inputs
    if not os.path.exists(args.json):
        print(f"[ERROR] JSON not found: {args.json}")
        sys.exit(1)
    if not os.path.exists(args.template):
        print(f"[ERROR] Template not found: {args.template}")
        sys.exit(1)

    # Load JSON
    with open(args.json, encoding="utf-8") as f:
        data = json.load(f)

    report_date = data.get("report_date", "unknown period")
    print(f"[INFO] Loaded JSON  : {args.json}")
    print(f"[INFO] Report period: {report_date}")
    print(f"[INFO] Template     : {args.template}")
    print(f"[INFO] Output       : {args.out}")
    print("[INFO] Generating Word document...")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    # Delete old file if it exists so the new one is always fresh
    if os.path.exists(args.out):
        os.remove(args.out)
        print("[INFO] Removed previous report.")

    gen = ReportGenerator(args.template)
    gen.generate_report(args.out, data)

    print(f"\n[DONE] Word report saved to:\n       {os.path.abspath(args.out)}")


if __name__ == "__main__":
    main()
