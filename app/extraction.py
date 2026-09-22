from __future__ import annotations

import base64

import pdfplumber

from app.state import GraphState, InvoiceDocument


def parse_pdf_node(state: GraphState) -> dict:
    pdf_path = state["pdf_path"]
    errors = list(state.get("errors", []))

    try:
        with pdfplumber.open(pdf_path) as pdf:
            text_parts = [page.extract_text() or "" for page in pdf.pages]
        raw_text = "\n".join(text_parts)
        if not raw_text.strip():
            errors.append("PDF parsed but no extractable text was found.")
    except Exception as exc:
        raw_text = ""
        errors.append(f"Failed to read PDF '{pdf_path}': {exc}")

    return {"raw_text": raw_text, "errors": errors}


def extract_with_gemini(raw_text: str, pdf_path: str) -> InvoiceDocument:
    from langchain_core.messages import HumanMessage
    from langchain_google_genai import ChatGoogleGenerativeAI

    llm = ChatGoogleGenerativeAI(model="gemini-3.6-flash", temperature=0)
    structured_llm = llm.with_structured_output(InvoiceDocument)

    with open(pdf_path, "rb") as f:
        pdf_base64 = base64.b64encode(f.read()).decode("utf-8")

    prompt_text = (
        "Extract the invoice data from the attached PDF into the given schema. "
        "Read the PDF visually as well as from any embedded text below, since "
        "some fields such as the seller's company name, address, or contact "
        "details may only be visible in the rendered page and not present in "
        "the extracted text, for example due to a broken font encoding. "
        "There are two distinct parties on this invoice: the seller (who "
        "issued the invoice and is owed payment) and the buyer/recipient "
        "(who is being billed). Any VAT ID explicitly labeled as belonging "
        "to the seller belongs to the sender. Any other company name, "
        "address, or VAT ID block, especially one with a different "
        "country's VAT ID format, belongs to the recipient, not the "
        "sender. Never assign the same company name or address to both "
        "sender and recipient. "
        "Numbers on this invoice use German formatting (period as "
        "thousands separator, comma as decimal separator, e.g. 2.100,00 "
        "means 2100.00) - convert every amount to a plain decimal number "
        "in the schema, do not copy the German-formatted string. "
        "This invoice does not print a VAT rate per line item. Assign "
        "vat_rate_pct yourself using standard German VAT rules: security "
        "deposits (Kaution, Mietkaution) are VAT-exempt pass-through "
        "amounts held in trust, so use 0 for those. Ordinary taxable "
        "goods and services (rent, service charges, parking, cleaning, "
        "etc.) use the standard German rate of 19 unless the invoice "
        "clearly indicates a reduced rate applies. Copy all other fields "
        "exactly as printed, including any numbers that look internally "
        "inconsistent, since arithmetic is validated separately "
        "downstream.\n\n"
        f"--- EXTRACTED PDF TEXT (may be incomplete) ---\n{raw_text}\n"
        "--- END EXTRACTED PDF TEXT ---"
    )

    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt_text},
            {"type": "file", "base64": pdf_base64, "mime_type": "application/pdf"},
        ]
    )
    return structured_llm.invoke([message])


def extract_document_node(state: GraphState) -> dict:
    raw_text = state.get("raw_text", "")
    pdf_path = state["pdf_path"]
    errors = list(state.get("errors", []))

    document = extract_with_gemini(raw_text, pdf_path)

    return {"document": document, "errors": errors}