import datetime
import logging
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from resolvr.config import GOOGLE_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

def parse_relative_date(date_text: str) -> str:
    """Normalize relative date string (e.g., 'last Tuesday') to YYYY-MM-DD.
    Uses Gemini for natural language dates.
    """
    date_text = date_text.strip()
    if not date_text:
        return ""
        
    # Check if already YYYY-MM-DD
    import re
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_text):
        return date_text
        
    if not GOOGLE_API_KEY:
        logger.warning("GOOGLE_API_KEY not set. Using local clock fallback.")
        return str(datetime.date.today())
        
    try:
        # LLM normalization call
        llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=0.0
        )
        
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %A")
        
        prompt = (
            f"Current date context: {current_time}.\n"
            f"Normalize the relative date expression '{date_text}' to ISO 8601 format (YYYY-MM-DD).\n"
            "Return only the normalized YYYY-MM-DD date string without any formatting, quotes, or conversational text. "
            "If it cannot be resolved, return the current date."
        )
        
        response = llm.invoke(prompt)
        raw_content = response.content
        if isinstance(raw_content, list):
            resolved_date = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in raw_content
            ).strip()
        else:
            resolved_date = str(raw_content).strip()
        logger.info(f"Normalized date '{date_text}' to '{resolved_date}' via Gemini.")
        
        # Verify result is YYYY-MM-DD
        if re.match(r'^\d{4}-\d{2}-\d{2}$', resolved_date):
            return resolved_date
            
        return str(datetime.date.today())
    except Exception as e:
        logger.error(f"Error normalizing date '{date_text}': {e}")
        return str(datetime.date.today())
