import logging
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from resolvr.config import GOOGLE_API_KEY, GEMINI_MODEL
from typing import Any
from resolvr.agent.state import AgentState

logger = logging.getLogger(__name__)

def classifier_node(state: AgentState) -> dict[str, Any]:
    """Node 1: Classify intent of user query and extract filter parameters."""
    logger.info("Classifier Node: Classifying user intent...")
    
    # Get last user message
    messages = state.get("messages", [])
    if not messages:
        return {"intent": "GENERAL", "thought_log": [{"node": "classifier", "type": "thought", "content": "No messages found, default to GENERAL."}]}
        
    last_user_message = messages[-1].content
    
    thought_log = []
    thought_log.append({
        "node": "classifier",
        "type": "thought",
        "content": f"Classifying query: '{last_user_message}'"
    })
    
    if not GOOGLE_API_KEY:
        logger.warning("GOOGLE_API_KEY not set. Defaulting to general intent.")
        return {
            "intent": "GENERAL",
            "thought_log": thought_log + [{"node": "classifier", "type": "observation", "content": "Gemini API key missing, default classification applied."}]
        }
        
    try:
        llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=0.0
        )
        
        prompt = (
            "You are the classification node of an agentic financial auditor.\n"
            "Given this user query: '{query}'\n"
            "Analyze the intent and extract details as JSON. Return ONLY raw JSON without formatting.\n"
            "JSON Fields:\n"
            "{{\n"
            "  \"intent\": \"One of: SUM (user wants to add up amounts), RECONCILE (user wants to cross-reference documents/receipts vs bank statement), ANOMALY_CHECK (user wants to audit duplicates or math errors), FILTER (user wants to search/retrieve specific transactions without sum), GENERAL (general query/chat)\",\n"
            "  \"merchant_filter\": \"extracted merchant name mentioned to filter on (string or null)\",\n"
            "  \"date_filter\": \"extracted relative or absolute date filter mentioned like 'last Tuesday' or 'Q3 2025' (string or null)\",\n"
            "  \"amount_filter\": \"extracted amount values or thresholds mentioned (number or null)\",\n"
            "  \"reasoning\": \"brief explanation of why this intent was selected\"\n"
            "}}"
        )
        
        formatted_prompt = prompt.format(query=last_user_message)
        response = llm.invoke(formatted_prompt)
        # response.content may be a list of parts in newer google-genai SDK versions
        raw_content = response.content
        if isinstance(raw_content, list):
            response_text = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in raw_content
            ).strip()
        else:
            response_text = str(raw_content).strip()
        
        # Clean response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
        data = json.loads(response_text)
        intent = data.get("intent", "GENERAL").upper()
        reasoning = data.get("reasoning", "Classification completed.")
        
        logger.info(f"Classifier intent: {intent}. Filters: Merchant={data.get('merchant_filter')}, Date={data.get('date_filter')}")
        
        thought_log.append({
            "node": "classifier",
            "type": "thought",
            "content": f"Classified intent: {intent}. Reasoning: {reasoning}"
        })
        
        # We store filters in state via retrieved_docs placeholders or metadata if needed, 
        # but the next Retriever node can inspect this state. We can store the filters 
        # in the returned dict, which LangGraph will merge into the state.
        return {
            "intent": intent,
            "thought_log": thought_log,
            # We can pass extraction params so the retriever can use them
            "classification_params": {
                "merchant_filter": data.get("merchant_filter"),
                "date_filter": data.get("date_filter"),
                "amount_filter": data.get("amount_filter")
            }
        }
    except Exception as e:
        logger.error(f"Error in classifier node: {e}")
        return {
            "intent": "GENERAL",
            "thought_log": thought_log + [{"node": "classifier", "type": "observation", "content": f"Classifier error: {e}. Defaulting to GENERAL."}]
        }
