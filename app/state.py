from __future__ import annotations

from decimal import Decimal
from typing import List, Optional, TypedDict

from pydantic import BaseModel, Field


class PartyInfo(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    vat_id: Optional[str] = None
    iban: Optional[str] = None
    bic: Optional[str] = None


class LineItem(BaseModel):
    description: str
    quantity: Decimal
    unit_price: Decimal
    vat_rate_pct: Decimal
    total_net: Decimal


class InvoiceTotals(BaseModel):
    net_total: Optional[Decimal] = None
    vat_total: Optional[Decimal] = None
    gross_total: Optional[Decimal] = None


class InvoiceDocument(BaseModel):
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    sender: PartyInfo = Field(default_factory=PartyInfo)
    recipient: PartyInfo = Field(default_factory=PartyInfo)
    line_items: List[LineItem] = Field(default_factory=list)
    totals: InvoiceTotals = Field(default_factory=InvoiceTotals)


class CheckResult(BaseModel):
    check_id: str
    description: str
    status: str
    details: str


class ValidationBlock(BaseModel):
    name: str
    status: str
    checks: List[CheckResult] = Field(default_factory=list)

    def finalize(self) -> "ValidationBlock":
        self.status = "FAILED" if any(c.status == "FAILED" for c in self.checks) else "PASSED"
        return self


class GraphState(TypedDict, total=False):
    pdf_path: str
    raw_text: str
    document: InvoiceDocument
    party_validation: ValidationBlock
    math_validation: ValidationBlock
    tax_validation: ValidationBlock
    errors: List[str]
    final_report: dict
