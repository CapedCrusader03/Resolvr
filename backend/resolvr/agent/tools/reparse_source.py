import os
import logging
import json
from typing import Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from resolvr.config import GOOGLE_API_KEY, GEMINI_MODEL
import base64

logger = logging.getLogger(__name__)

def reparse_document_total(
    file_path: str,
    page_number: int = 1,
    anomaly_desc: str = ""
) -> dict[str, Any]:
    """Re-reads the document using Gemini Vision to resolve a specific anomaly (e.g., OCR total mismatch).
    It asks the model to pay extra attention to the totals area.
    """
    if not GOOGLE_API_KEY:
        raise ValueError("Google API Key is required for re-parsing scanned documents.")
        
    try:
        from pdf2image import convert_from_path
    except ImportError:
        logger.error("pdf2image library is not installed.")
        raise ImportError("pdf2image is required for visual re-parsing.")

    logger.info(f"Re-parsing document {file_path} page {page_number} to resolve: {anomaly_desc}")
    
    # Render only the target page
    pages = convert_from_path(
        file_path,
        first_page=page_number,
        last_page=page_number
    )
    
    if not pages:
        raise ValueError(f"Could not render page {page_number} from document.")
        
    page = pages[0]
    
    # We can crop the image or send it full size with instructions to focus.
    # Cropping to bottom half/third can increase accuracy for totals.
    width, height = page.size
    # Focus area: bottom half
    bottom_half = page.crop((0, int(height * 0.5), width, height))
    
    temp_img_path = f"{file_path}_reparse_p{page_number}.jpg"
    bottom_half.save(temp_img_path, "JPEG")
    
    try:
        # Encode image
        with open(temp_img_path, "rb") as image_file:
            base64_img = base64.b64encode(image_file.read()).decode("utf-8")
            
        llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=0.0
        )
        
        prompt = (
            f"You are an auditor double-checking an OCR anomaly: '{anomaly_desc}'.\n"
            "Here is the bottom half of the document page containing totals. "
            "Inspect the values with surgical precision. Re-read the transaction total, "
            "subtotal, taxes, and any handwritten notes.\n"
            "Return a JSON object containing the correct total amount and a short explanation of your observation. "
            "Return ONLY the raw JSON object, without markdown formatting or code blocks.\n"
            "Format:\n"
            "{\n"
            "  \"total_amount\": \"the corrected total amount as a float (number, or null)\",\n"
            "  \"observation\": \"short explanation of what you found (string)\",\n"
            "  \"confidence\": \"confidence score between 0.0 and 1.0 (number)\"\n"
            "}"
        )
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}
                }
            ]
        )
        
        response = llm.invoke([message])
        response_text = response.content.strip()
        
        # Clean response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
            
        data = json.loads(response_text)
        logger.info(f"Re-parse completed. Result: {data}")
        return data
        
    finally:
        if os.path.exists(temp_img_path):
            os.remove(temp_img_path)
