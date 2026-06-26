import logging
from typing import Literal, Any

from langgraph.graph import StateGraph, END

from resolvr.agent.state import AgentState
from resolvr.agent.nodes.classifier import classifier_node
from resolvr.agent.nodes.retriever import retriever_node
from resolvr.agent.nodes.calculator import calculator_node
from resolvr.agent.nodes.anomaly_detector import anomaly_detector_node
from resolvr.agent.nodes.solver import solver_node
from resolvr.agent.nodes.reporter import reporter_node
from resolvr.memory.session_store import get_session_checkpointer

logger = logging.getLogger(__name__)

# Routing conditional edges
def route_retriever(state: AgentState) -> Literal["calculator", "reporter"]:
    """Route from retriever node based on intent."""
    intent = state.get("intent", "GENERAL")
    if intent in ["SUM", "RECONCILE"]:
        return "calculator"
    return "reporter"

def route_anomaly_detector(state: AgentState) -> Literal["solver", "reporter"]:
    """Route from anomaly detector node based on whether anomalies are found."""
    anomalies = state.get("anomalies", [])
    if anomalies:
        return "solver"
    return "reporter"

def route_solver(state: AgentState) -> Literal["solver", "reporter"]:
    """Loop solver node or exit to reporter based on remaining anomalies and safety guard."""
    anomalies = state.get("anomalies", [])
    iteration_count = state.get("iteration_count", 0)
    
    if anomalies and iteration_count < 3:
        logger.info(f"Solver Node looping: {len(anomalies)} anomalies remaining. Iteration: {iteration_count}")
        return "solver"
        
    logger.info("Solver Node exiting to reporter.")
    return "reporter"

def build_workflow_graph() -> StateGraph:
    """Build and compile the LangGraph workflow state machine."""
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("classifier", classifier_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("calculator", calculator_node)
    workflow.add_node("anomaly_detector", anomaly_detector_node)
    workflow.add_node("solver", solver_node)
    workflow.add_node("reporter", reporter_node)
    
    # Set Entry Point
    workflow.set_entry_point("classifier")
    
    # Add Fixed Edges
    workflow.add_edge("classifier", "retriever")
    workflow.add_edge("calculator", "anomaly_detector")
    
    # Add Conditional Edges
    workflow.add_conditional_edges(
        "retriever",
        route_retriever,
        {
            "calculator": "calculator",
            "reporter": "reporter"
        }
    )
    
    workflow.add_conditional_edges(
        "anomaly_detector",
        route_anomaly_detector,
        {
            "solver": "solver",
            "reporter": "reporter"
        }
    )
    
    workflow.add_conditional_edges(
        "solver",
        route_solver,
        {
            "solver": "solver",
            "reporter": "reporter"
        }
    )
    
    workflow.add_edge("reporter", END)
    
    # Compile with persistence saver checkpointer
    checkpointer = get_session_checkpointer()
    compiled_graph = workflow.compile(checkpointer=checkpointer)
    logger.info("LangGraph workflow graph compiled successfully.")
    return compiled_graph
