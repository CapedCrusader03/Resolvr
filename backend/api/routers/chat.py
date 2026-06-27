import json
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage

from resolvr.agent.graph import build_workflow_graph

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    query: str
    session_id: str

# Instantiate the compiled graph once at module load
workflow_graph = build_workflow_graph()

# Helper: safely extract text from an LLM content that may be str or list-of-parts
def _extract_token(chunk_content) -> str:
    if isinstance(chunk_content, list):
        return "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in chunk_content
        )
    return str(chunk_content) if chunk_content else ""

NODE_NAMES = {"classifier", "retriever", "calculator", "anomaly_detector", "solver", "reporter"}

@router.post("")
async def chat_endpoint(request: ChatRequest):
    """Start the LangGraph auditor process and stream thoughts & citations via Server-Sent Events."""

    query = request.query
    session_id = request.session_id

    if not query.strip() or not session_id.strip():
        raise HTTPException(status_code=400, detail="Query and session_id are required.")

    config = {"configurable": {"thread_id": session_id}}

    async def sse_event_generator():
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
            "final_answer": "",
        }

        streamed_any_answer = False
        final_answer_fallback = ""

        try:
            # astream_events yields dicts with keys: event, name, data, ...
            async for event_obj in workflow_graph.astream_events(inputs, config=config, version="v2"):
                event_type = event_obj.get("event", "")
                event_name = event_obj.get("name", "")
                data = event_obj.get("data", {}) or {}

                # ── 1. Node finished → emit thought_log and citations ──────────
                if event_type == "on_chain_end" and event_name in NODE_NAMES:
                    output = data.get("output") or {}
                    if not isinstance(output, dict):
                        output = {}

                    # Emit thought entries
                    for thought in output.get("thought_log", []):
                        yield f"data: {json.dumps({'type': 'thought', 'node': event_name, 'content': thought.get('content', ''), 'thought_type': thought.get('type', 'thought')})}\n\n"

                    # Emit citations from retriever
                    if event_name == "retriever":
                        for citation in output.get("citations", []):
                            yield f"data: {json.dumps({'type': 'citation', 'filename': citation.get('filename', ''), 'page_number': citation.get('page_number'), 'row_number': citation.get('row_number'), 'confidence': citation.get('confidence', 0.9)})}\n\n"

                    # Capture final_answer for fallback (reporter node)
                    if event_name == "reporter" and output.get("final_answer"):
                        final_answer_fallback = output["final_answer"]

                # ── 2. LLM streaming tokens → emit answer chunks ─────────────
                elif event_type == "on_chat_model_stream":
                    chunk = data.get("chunk")
                    token = ""
                    if chunk is not None:
                        token = _extract_token(chunk.content)
                    if token:
                        streamed_any_answer = True
                        yield f"data: {json.dumps({'type': 'answer_chunk', 'content': token})}\n\n"

            # ── 3. Fallback: if no streaming tokens arrived, emit final_answer ─
            if not streamed_any_answer and final_answer_fallback:
                yield f"data: {json.dumps({'type': 'answer_chunk', 'content': final_answer_fallback})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.error(f"Error in chat SSE streaming: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(sse_event_generator(), media_type="text/event-stream")
