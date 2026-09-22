import os
import sys
from decimal import Decimal

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.state import InvoiceDocument, InvoiceTotals, LineItem, PartyInfo
from app.validators.math_validation import validate_math_node
from app.validators.party_validation import validate_parties_node
from app.validators.tax_validation import validate_tax_node


def _clean_document() -> InvoiceDocument:
    return InvoiceDocument(
        invoice_number="INV-TEST-001",
        sender=PartyInfo(
            name="Test Sender GmbH",
            address="Teststraße 1, 12345 Berlin",
            email="a@b.com",
            vat_id="DE123456789",
            iban="DE89370400440532013000",
            bic="COBADEFFXXX",
        ),
        recipient=PartyInfo(name="Test Customer", address="Customer Str 2", vat_id="DE999999999"),
        line_items=[
            LineItem(description="Item A", quantity=1, unit_price=Decimal("100.00"),
                      vat_rate_pct=Decimal("19"), total_net=Decimal("100.00")),
            LineItem(description="Item B", quantity=2, unit_price=Decimal("50.00"),
                      vat_rate_pct=Decimal("7"), total_net=Decimal("100.00")),
        ],
        totals=InvoiceTotals(
            net_total=Decimal("200.00"),
            vat_total=Decimal("26.00"),
            gross_total=Decimal("226.00"),
        ),
    )


def test_party_validation_passes_on_clean_document():
    result = validate_parties_node({"document": _clean_document()})
    assert result["party_validation"].status == "PASSED"


def test_party_validation_flags_missing_recipient_vat_id():
    doc = _clean_document()
    doc.recipient.vat_id = None
    result = validate_parties_node({"document": doc})
    assert result["party_validation"].status == "FAILED"
    failed_ids = [c.check_id for c in result["party_validation"].checks if c.status == "FAILED"]
    assert "recipient.vat_id" in failed_ids


def test_math_validation_passes_on_clean_document():
    result = validate_math_node({"document": _clean_document()})
    assert result["math_validation"].status == "PASSED"


def test_math_validation_flags_line_item_mismatch():
    doc = _clean_document()
    doc.line_items[1].total_net = Decimal("999.00")
    result = validate_math_node({"document": doc})
    assert result["math_validation"].status == "FAILED"


def test_math_validation_flags_aggregation_mismatch():
    doc = _clean_document()
    doc.totals.net_total = Decimal("999.00")
    result = validate_math_node({"document": doc})
    failed_ids = [c.check_id for c in result["math_validation"].checks if c.status == "FAILED"]
    assert "aggregation.net_total" in failed_ids


def test_tax_validation_passes_on_clean_document():
    result = validate_tax_node({"document": _clean_document()})
    assert result["tax_validation"].status == "PASSED"


def test_tax_validation_flags_vat_sum_mismatch():
    doc = _clean_document()
    doc.totals.vat_total = Decimal("50.00")
    result = validate_tax_node({"document": doc})
    assert result["tax_validation"].status == "FAILED"


def test_tax_validation_flags_gross_mismatch():
    doc = _clean_document()
    doc.totals.gross_total = Decimal("500.00")
    result = validate_tax_node({"document": doc})
    failed_ids = [c.check_id for c in result["tax_validation"].checks if c.status == "FAILED"]
    assert "gross_check" in failed_ids


def test_tax_validation_flags_nonstandard_rate():
    doc = _clean_document()
    doc.line_items[0].vat_rate_pct = Decimal("15")
    result = validate_tax_node({"document": doc})
    failed_ids = [c.check_id for c in result["tax_validation"].checks if c.status == "FAILED"]
    assert "line_item.1.vat_rate_valid" in failed_ids
