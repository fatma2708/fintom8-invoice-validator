from __future__ import annotations

import json
from decimal import Decimal

from app.state import GraphState


def _json_default(obj):
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError(f"Not JSON serializable: {obj!r}")


def generate_report_node(state: GraphState) -> dict:
    document = state["document"]
    blocks = [state["party_validation"], state["math_validation"], state["tax_validation"]]
    overall_status = "FAILED" if any(b.status == "FAILED" for b in blocks) else "PASSED"

    report = {
        "invoice_number": document.invoice_number,
        "overall_status": overall_status,
        "extraction_errors": state.get("errors", []),
        "extracted_document": document.model_dump(),
        "validation": {
            "sender_recipient_data": state["party_validation"].model_dump(),
            "mathematical_calculations": state["math_validation"].model_dump(),
            "tax_calculation_anomaly_detection": state["tax_validation"].model_dump(),
        },
    }
    return {"final_report": report}


def print_report(report: dict) -> None:
    bar = "=" * 72
    print(bar)
    print(" FINTOM8 PRE-ERP INVOICE VALIDATION REPORT")
    print(f" Invoice: {report.get('invoice_number')}")
    print(f" Overall status: {report['overall_status']}")
    print(bar)

    if report.get("extraction_errors"):
        print("\n[!] Extraction warnings:")
        for err in report["extraction_errors"]:
            print(f"   - {err}")

    for key, label in [
        ("sender_recipient_data", "1) Sender & Recipient Data"),
        ("mathematical_calculations", "2) Mathematical Calculations"),
        ("tax_calculation_anomaly_detection", "3) Tax Calculation & Anomaly Detection"),
    ]:
        block = report["validation"][key]
        print(f"\n--- {label}: {block['status']} ---")
        for check in block["checks"]:
            mark = "PASS" if check["status"] == "PASSED" else "FAIL"
            print(f"  [{mark}] {check['description']}")
            print(f"        {check['details']}")

    print("\n" + bar)


def report_to_json(report: dict) -> str:
    return json.dumps(report, indent=2, default=_json_default, ensure_ascii=False)
