import logging
from typing import Any
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

def supervisor_node(state: AgentState) -> dict[str, Any]:
    """Node 0: Supervisor Agent that coordinates execution and tracks the audit thought timeline."""
    logger.info("Supervisor Agent: Evaluating audit status...")
    
    # We inspect what nodes have run by checking who has written to the thought log.
    nodes_run = {t.get("node") for t in state.get("thought_log", []) if t.get("node")}
    intent = state.get("intent", "GENERAL")
    
    thought_log = []
    
    # Simple state evaluation mapping
    target = "classifier"
    if "classifier" in nodes_run:
        if "retriever" not in nodes_run:
            target = "retriever"
        else:
            needs_calc = intent in ["SUM", "RECONCILE", "ANOMALY_CHECK"]
            if needs_calc and "calculator" not in nodes_run:
                target = "calculator"
            elif needs_calc and "anomaly_detector" not in nodes_run:
                target = "anomaly_detector"
            elif state.get("anomalies", []) and state.get("iteration_count", 0) < 3:
                target = "solver"
            else:
                target = "reporter"
                
    thought_log.append({
        "node": "supervisor",
        "type": "thought",
        "content": f"Supervisor Node: Routing control to specialized worker: '{target}'."
    })
    
    return {
        "thought_log": thought_log
    }

def route_supervisor(state: AgentState) -> str:
    """Orchestrate state machine transitions dynamically from the Supervisor state."""
    nodes_run = {t.get("node") for t in state.get("thought_log", []) if t.get("node")}
    intent = state.get("intent", "GENERAL")
    
    if "classifier" not in nodes_run:
        return "classifier"
        
    if "retriever" not in nodes_run:
        return "retriever"
        
    needs_calc = intent in ["SUM", "RECONCILE", "ANOMALY_CHECK"]
    if needs_calc and "calculator" not in nodes_run:
        return "calculator"
        
    if needs_calc and "anomaly_detector" not in nodes_run:
        return "anomaly_detector"
        
    # Anomaly visual crop-and-reparse ReAct loop (max 3 iterations)
    anomalies = state.get("anomalies", [])
    iteration_count = state.get("iteration_count", 0)
    if anomalies and iteration_count < 3:
        return "solver"
        
    return "reporter"

def build_workflow_graph() -> StateGraph:
    """Build and compile the LangGraph workflow state machine using a Supervisor topology."""
    workflow = StateGraph(AgentState)
    
    # Add Nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("classifier", classifier_node)
    workflow.add_node("retriever", retriever_node)
    workflow.add_node("calculator", calculator_node)
    workflow.add_node("anomaly_detector", anomaly_detector_node)
    workflow.add_node("solver", solver_node)
    workflow.add_node("reporter", reporter_node)
    
    # Set Entry Point
    workflow.set_entry_point("supervisor")
    
    # Add Fixed Edges: Workers return control back to the Supervisor
    workflow.add_edge("classifier", "supervisor")
    workflow.add_edge("retriever", "supervisor")
    workflow.add_edge("calculator", "supervisor")
    workflow.add_edge("anomaly_detector", "supervisor")
    workflow.add_edge("solver", "supervisor")
    
    # Add Conditional Edges from the Supervisor to delegable agents
    workflow.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            "classifier": "classifier",
            "retriever": "retriever",
            "calculator": "calculator",
            "anomaly_detector": "anomaly_detector",
            "solver": "solver",
            "reporter": "reporter"
        }
    )
    
    # The reporter node finishes execution
    workflow.add_edge("reporter", END)
    
    # Compile with persistence saver checkpointer
    checkpointer = get_session_checkpointer()
    compiled_graph = workflow.compile(checkpointer=checkpointer)
    logger.info("LangGraph workflow graph compiled successfully in Supervisor-Worker topology.")
    return compiled_graph
