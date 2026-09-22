# Fintom8 Pre-ERP Invoice Validator

A LangGraph agent that ingests a real-estate invoice PDF and runs three
validation criteria against it: sender/recipient data completeness,
line-item and aggregation math, and VAT calculation with anomaly detection.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Place your invoice PDF at `data/invoice.pdf`, or pass a path directly.

`GOOGLE_API_KEY` in `.env` is required. Extraction uses Gemini
(`gemini-3.6-flash` via `langchain-google-genai`) with structured output.

## Run

```bash
python main.py
python main.py path/to/other_invoice.pdf
```

Prints a terminal report and writes `validation_report.json` with the full
structured payload. Exit code is 0 if every check passed, 2 otherwise.

## Tests

```bash
python -m pytest tests/ -v
```

Nine unit tests exercise each validator directly against hand-built
`InvoiceDocument` objects, no PDF or LLM call involved.

## Graph structure

```
START -> parse_pdf -> extract_document -> validate_parties     -> generate_report -> END
                                        -> validate_math        ->
                                        -> validate_tax         ->
```

`extract_document` fans out to the three validators, which only read
`document` from shared state and have no dependency on each other or on
ordering. `generate_report` fans back in once all three have run, so every
criterion is always evaluated in full rather than short-circuited on the
first failure.

## Validation logic

| Criterion | Checks |
|---|---|
| Sender & Recipient | sender name/address/contact present; sender VAT ID / IBAN / BIC format-valid; recipient name/address/VAT ID present |
| Mathematical Calculations | per line: Total Net == Qty x Unit Price; sum(line Total Net) == stated Net Total |
| Tax Calculation & Anomaly Detection | per line: VAT rate in {0%, 7%, 19%}; recomputed VAT (Total Net x rate) summed and compared to stated VAT Total; Net Total + VAT Total == Gross Total |

All monetary comparisons use `Decimal` with a 0.01 tolerance.

## Project layout

```
main.py
requirements.txt
.env.example
app/
  state.py
  extraction.py
  graph.py
  report.py
  validators/
    party_validation.py
    math_validation.py
    tax_validation.py
tests/
  test_validators.py
data/
  invoice.pdf
```

## Future extensions

- Auto-repair: route FAILED math/tax checks to a correction node that
  re-derives totals from the trustworthy line items and re-validates.
- EN16931 / Schematron validation once the payload is normalized, as an
  additional graph branch ahead of ERP ingestion.
- ERP export: map a PASSED `InvoiceDocument` into a SAP/DATEV staging
  payload; route FAILED documents to a human-review queue instead.
- Confidence scoring on the Gemini extraction path, flagging low-confidence
  fields for manual review even when the arithmetic checks pass.
