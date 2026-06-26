import json
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from resolvr.agent.graph import build_workflow_graph
from resolvr.schemas.models import ChatMessage

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    query: str
    session_id: str

# Instantiate the compiled graph once
workflow_graph = build_workflow_graph()

@router.post("")
async def chat_endpoint(request: ChatRequest):
    """Start the LangGraph auditor process and stream thoughts & citations via Server-Sent Events."""
    
    query = request.query
    session_id = request.session_id
    
    if not query.strip() or not session_id.strip():
        raise HTTPException(status_code=400, detail="Query and session_id are required.")

    # Configure graph execution connection (persistence checkpoint thread)
    config = {"configurable": {"thread_id": session_id}}
    
    async def sse_event_generator():
        # Set up state inputs
        inputs = {
            "messages": [HumanMessage(content=query)],
            "session_id": session_id,
            "intent": "GENERAL",
            "retrieved_docs": [],
            "calculation_result": None,
            "anomalies": [],
            "solved_anomalies": [],
            "citations": [],
            "thought_log": [],
            "iteration_count": 0,
            "final_answer": ""
        }
        
        # Track which node's thoughts we've already yielded to avoid duplicates
        yielded_thoughts_count = 0
        
        try:
            # Run graph streaming events (v2 is standard)
            async for event, data in workflow_graph.astream_events(inputs, config=config, version="v2"):
                # 1. Capture node executions to stream thought steps
                # When a node finishes running, it outputs its state update in 'on_chain_end'
                # for the node name. Or we can monitor state updates.
                if event == "on_chain_end" and data.get("name") in ["classifier", "retriever", "calculator", "anomaly_detector", "solver", "reporter"]:
                    node_name = data["name"]
                    output = data.get("output", {})
                    
                    if output and "thought_log" in output:
                        node_thoughts = output["thought_log"]
                        # Yield new thoughts
                        for thought in node_thoughts:
                            yield f"data: {json.dumps({'type': 'thought', 'node': node_name, 'content': thought['content'], 'thought_type': thought['type']})}\n\n"
                            
                    # Yield citations if retriever finished
                    if node_name == "retriever" and output and "citations" in output:
                        for citation in output["citations"]:
                            yield f"data: {json.dumps({'type': 'citation', 'filename': citation['filename'], 'page_number': citation.get('page_number'), 'row_number': citation.get('row_number'), 'confidence': citation.get('confidence', 0.9)})}\n\n"
                            
                # 2. Capture token streams from Gemini in the reporter node for the final answer
                elif event == "on_chat_model_stream":
                    # Stream tokens token-by-token
                    token = data.get("chunk", {}).content
                    if token:
                        yield f"data: {json.dumps({'type': 'answer_chunk', 'content': token})}\n\n"
                        
            # Yield final completion signal
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
        except Exception as e:
            logger.error(f"Error in chat SSE streaming: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            
    return StreamingResponse(sse_event_generator(), media_type="text/event-stream")
