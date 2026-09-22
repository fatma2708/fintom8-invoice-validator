from __future__ import annotations

from decimal import Decimal

from app.state import CheckResult, GraphState, ValidationBlock

TOLERANCE = Decimal("0.01")


def validate_math_node(state: GraphState) -> dict:
    document = state["document"]
    checks: list[CheckResult] = []

    if not document.line_items:
        checks.append(
            CheckResult(
                check_id="line_items.presence",
                description="Line items extracted",
                status="FAILED",
                details="No line items were found on the invoice.",
            )
        )
        block = ValidationBlock(name="Mathematical Calculations", status="FAILED", checks=checks).finalize()
        return {"math_validation": block}

    computed_net_sum = Decimal("0")
    for idx, item in enumerate(document.line_items, start=1):
        expected_total = (item.quantity * item.unit_price).quantize(Decimal("0.01"))
        printed_total = item.total_net.quantize(Decimal("0.01"))
        diff = abs(expected_total - printed_total)
        ok = diff <= TOLERANCE

        checks.append(
            CheckResult(
                check_id=f"line_item.{idx}.math",
                description=f"Line {idx} ('{item.description}') Total Net = Qty x Unit Price",
                status="PASSED" if ok else "FAILED",
                details=(
                    f"Qty {item.quantity} x Unit Price {item.unit_price} = {expected_total}; "
                    f"printed Total Net = {printed_total}"
                    + ("" if ok else f"  -> discrepancy of {diff}")
                ),
            )
        )
        computed_net_sum += printed_total

    stated_net_total = document.totals.net_total
    if stated_net_total is None:
        checks.append(
            CheckResult(
                check_id="aggregation.net_total",
                description="Sum of line items matches stated Net Total",
                status="FAILED",
                details="No Net Total was found on the invoice.",
            )
        )
    else:
        diff = abs(computed_net_sum - stated_net_total.quantize(Decimal("0.01")))
        ok = diff <= TOLERANCE
        checks.append(
            CheckResult(
                check_id="aggregation.net_total",
                description="Sum of line items matches stated Net Total",
                status="PASSED" if ok else "FAILED",
                details=(
                    f"Sum of printed line-item Total Net = {computed_net_sum}; "
                    f"stated Net Total = {stated_net_total}"
                    + ("" if ok else f"  -> discrepancy of {diff}")
                ),
            )
        )

    block = ValidationBlock(name="Mathematical Calculations", status="PASSED", checks=checks).finalize()
    return {"math_validation": block}
