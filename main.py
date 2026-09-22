from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv

from app.graph import build_graph
from app.report import print_report, report_to_json

DEFAULT_PDF = os.path.join(os.path.dirname(__file__), "data", "invoice.pdf")


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Fintom8 Pre-ERP Invoice Validator")
    parser.add_argument("pdf_path", nargs="?", default=DEFAULT_PDF, help="Path to the invoice PDF")
    parser.add_argument(
        "--json-out",
        default="validation_report.json",
        help="Path to write the full JSON report",
    )
    args = parser.parse_args()

    if not os.path.exists(args.pdf_path):
        print(f"ERROR: PDF not found at {args.pdf_path}", file=sys.stderr)
        sys.exit(1)

    app = build_graph()
    result = app.invoke({"pdf_path": args.pdf_path})
    report = result["final_report"]

    print_report(report)

    with open(args.json_out, "w", encoding="utf-8") as f:
        f.write(report_to_json(report))
    print(f"\nFull structured report written to: {args.json_out}")

    sys.exit(0 if report["overall_status"] == "PASSED" else 2)


if __name__ == "__main__":
    main()
