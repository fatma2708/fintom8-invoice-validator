from __future__ import annotations

from langgraph.graph import END, StateGraph

from app.extraction import extract_document_node, parse_pdf_node
from app.report import generate_report_node
from app.state import GraphState
from app.validators.math_validation import validate_math_node
from app.validators.party_validation import validate_parties_node
from app.validators.tax_validation import validate_tax_node


def build_graph():
    graph = StateGraph(GraphState)

    graph.add_node("parse_pdf", parse_pdf_node)
    graph.add_node("extract_document", extract_document_node)
    graph.add_node("validate_parties", validate_parties_node)
    graph.add_node("validate_math", validate_math_node)
    graph.add_node("validate_tax", validate_tax_node)
    graph.add_node("generate_report", generate_report_node)

    graph.set_entry_point("parse_pdf")
    graph.add_edge("parse_pdf", "extract_document")

    graph.add_edge("extract_document", "validate_parties")
    graph.add_edge("extract_document", "validate_math")
    graph.add_edge("extract_document", "validate_tax")

    graph.add_edge("validate_parties", "generate_report")
    graph.add_edge("validate_math", "generate_report")
    graph.add_edge("validate_tax", "generate_report")

    graph.add_edge("generate_report", END)

    return graph.compile()
