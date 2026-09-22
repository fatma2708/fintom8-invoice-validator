from __future__ import annotations

import re

from app.state import CheckResult, GraphState, ValidationBlock

VAT_ID_PATTERN = re.compile(r"^DE\d{9}$")
IBAN_PATTERN = re.compile(r"^[A-Z]{2}\d{2}[A-Z0-9]{10,30}$")
BIC_PATTERN = re.compile(r"^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$")


def _presence_check(check_id: str, label: str, value) -> CheckResult:
    ok = bool(value and str(value).strip())
    return CheckResult(
        check_id=check_id,
        description=f"{label} present",
        status="PASSED" if ok else "FAILED",
        details=f"{label} = {value!r}" if ok else f"{label} is missing from the invoice.",
    )


def _format_check(check_id: str, label: str, value, pattern: re.Pattern) -> CheckResult:
    if not value:
        return CheckResult(
            check_id=check_id,
            description=f"{label} format valid",
            status="FAILED",
            details=f"{label} is missing, cannot validate format.",
        )
    normalized = str(value).replace(" ", "")
    ok = bool(pattern.match(normalized))
    return CheckResult(
        check_id=check_id,
        description=f"{label} format valid",
        status="PASSED" if ok else "FAILED",
        details=(
            f"{label} '{value}' matches expected format."
            if ok
            else f"{label} '{value}' does not match the expected pattern."
        ),
    )


def validate_parties_node(state: GraphState) -> dict:
    document = state["document"]
    sender = document.sender
    recipient = document.recipient

    checks = [
        _presence_check("sender.name", "Sender company name", sender.name),
        _presence_check("sender.address", "Sender address", sender.address),
        _presence_check(
            "sender.contact",
            "Sender contact info (email or phone)",
            sender.email or sender.phone,
        ),
        _format_check("sender.vat_id", "Sender German VAT ID", sender.vat_id, VAT_ID_PATTERN),
        _format_check("sender.iban", "Sender IBAN", sender.iban, IBAN_PATTERN),
        _format_check("sender.bic", "Sender BIC", sender.bic, BIC_PATTERN),
        _presence_check("recipient.name", "Recipient customer name", recipient.name),
        _presence_check("recipient.address", "Recipient full address", recipient.address),
        _presence_check("recipient.vat_id", "Recipient VAT ID", recipient.vat_id),
    ]

    block = ValidationBlock(name="Sender & Recipient Data", status="PASSED", checks=checks).finalize()
    return {"party_validation": block}
