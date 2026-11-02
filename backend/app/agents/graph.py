from langgraph.graph import StateGraph, START, END
from app.agents.state import DocuMindState
from app.agents.nodes import (
    intake_agent_node,
    ocr_agent_node,
    classification_agent_node,
    extraction_agent_node,
    validation_agent_node,
    duplicate_detection_agent_node,
    anomaly_detection_agent_node,
    decision_agent_node,
    finalization_agent_node
)
from app.core.logging import logger


def build_documind_workflow():
    """
    Constructs the 9-Agent DocuMind LangGraph orchestration pipeline.
    """
    workflow = StateGraph(DocuMindState)

    # Add Nodes
    workflow.add_node("intake", intake_agent_node)
    workflow.add_node("ocr", ocr_agent_node)
    workflow.add_node("classification", classification_agent_node)
    workflow.add_node("extraction", extraction_agent_node)
    workflow.add_node("validation", validation_agent_node)
    workflow.add_node("duplicate_detection", duplicate_detection_agent_node)
    workflow.add_node("anomaly_detection", anomaly_detection_agent_node)
    workflow.add_node("decision", decision_agent_node)
    workflow.add_node("finalization", finalization_agent_node)

    # Define Linear & Conditional Flow
    workflow.add_edge(START, "intake")
    workflow.add_edge("intake", "ocr")
    workflow.add_edge("ocr", "classification")
    workflow.add_edge("classification", "extraction")
    workflow.add_edge("extraction", "validation")
    workflow.add_edge("validation", "duplicate_detection")
    workflow.add_edge("duplicate_detection", "anomaly_detection")
    workflow.add_edge("anomaly_detection", "decision")
    workflow.add_edge("decision", "finalization")
    workflow.add_edge("finalization", END)

    app = workflow.compile()
    return app


# Singleton compiled graph instance
documind_app = build_documind_workflow()


def execute_document_workflow(initial_state: DocuMindState) -> DocuMindState:
    """
    Executes the complete multi-agent pipeline for an uploaded document.
    """
    logger.info(f"Initiating DocuMind multi-agent workflow for document {initial_state.get('document_id')}")
    final_state = documind_app.invoke(initial_state)
    logger.info(f"Completed DocuMind workflow for document {initial_state.get('document_id')} with status: {final_state.get('current_step')}")
    return final_state

