from __future__ import annotations

from decimal import Decimal

from app.state import CheckResult, GraphState, ValidationBlock

TOLERANCE = Decimal("0.01")
VALID_GERMAN_VAT_RATES = {Decimal("19"), Decimal("7"), Decimal("0")}


def validate_tax_node(state: GraphState) -> dict:
    document = state["document"]
    checks: list[CheckResult] = []

    computed_vat_sum = Decimal("0")

    for idx, item in enumerate(document.line_items, start=1):
        rate = item.vat_rate_pct
        printed_net = item.total_net.quantize(Decimal("0.01"))
        expected_vat = (printed_net * rate / Decimal("100")).quantize(Decimal("0.01"))

        rate_ok = rate in VALID_GERMAN_VAT_RATES
        checks.append(
            CheckResult(
                check_id=f"line_item.{idx}.vat_rate_valid",
                description=f"Line {idx} ('{item.description}') uses a standard German VAT rate",
                status="PASSED" if rate_ok else "FAILED",
                details=(
                    f"Rate {rate}% is within {{0, 7, 19}}%."
                    if rate_ok
                    else f"Rate {rate}% is not a standard German VAT rate (0% / 7% / 19%)."
                ),
            )
        )

        checks.append(
            CheckResult(
                check_id=f"line_item.{idx}.vat_amount",
                description=f"Line {idx} recomputed VAT ({rate}% of Total Net)",
                status="PASSED",
                details=f"{printed_net} x {rate}% = {expected_vat}",
            )
        )
        computed_vat_sum += expected_vat

    stated_vat_total = document.totals.vat_total
    if stated_vat_total is None:
        checks.append(
            CheckResult(
                check_id="tax_sum.vat_total",
                description="Recomputed VAT sum matches stated VAT Total",
                status="FAILED",
                details="No VAT Total was found on the invoice.",
            )
        )
    else:
        diff = abs(computed_vat_sum - stated_vat_total.quantize(Decimal("0.01")))
        ok = diff <= TOLERANCE
        checks.append(
            CheckResult(
                check_id="tax_sum.vat_total",
                description="Recomputed VAT sum matches stated VAT Total",
                status="PASSED" if ok else "FAILED",
                details=(
                    f"Sum of recomputed per-line VAT = {computed_vat_sum}; "
                    f"stated VAT Total = {stated_vat_total}"
                    + ("" if ok else f"  -> discrepancy of {diff}")
                ),
            )
        )

    net_total = document.totals.net_total
    vat_total = document.totals.vat_total
    gross_total = document.totals.gross_total
    if net_total is None or vat_total is None or gross_total is None:
        checks.append(
            CheckResult(
                check_id="gross_check",
                description="Net Total + VAT Total = Gross Total",
                status="FAILED",
                details="One or more of Net Total / VAT Total / Gross Total is missing.",
            )
        )
    else:
        expected_gross = (net_total + vat_total).quantize(Decimal("0.01"))
        diff = abs(expected_gross - gross_total.quantize(Decimal("0.01")))
        ok = diff <= TOLERANCE
        checks.append(
            CheckResult(
                check_id="gross_check",
                description="Net Total + VAT Total = Gross Total",
                status="PASSED" if ok else "FAILED",
                details=(
                    f"{net_total} + {vat_total} = {expected_gross}; stated Gross Total = {gross_total}"
                    + ("" if ok else f"  -> discrepancy of {diff}")
                ),
            )
        )

    block = ValidationBlock(name="Tax Calculation & Anomaly Detection", status="PASSED", checks=checks).finalize()
    return {"tax_validation": block}
