import base64
import json
import logging
import os
from typing import dict, Any, list
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from resolvr.config import GOOGLE_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

def encode_image(image_path: str) -> str:
    """Encode local image to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def parse_scanned_pdf_with_gemini(file_path: str) -> dict[str, Any]:
    """Render PDF pages to images and parse using Gemini Vision API."""
    if not GOOGLE_API_KEY:
        logger.warning("GOOGLE_API_KEY not set. Vision parser will fail.")
        raise ValueError("Google API Key is required for scanned PDFs.")
        
    try:
        from pdf2image import convert_from_path
    except ImportError:
        logger.error("pdf2image library is not installed. Scanned PDF parsing will fail.")
        raise ImportError("pdf2image is required for scanned PDFs. Install poppler and pdf2image.")

    try:
        # Convert PDF pages to PIL images
        # We process at most first 3 pages to avoid rate limits/timeouts in demo
        logger.info(f"Converting PDF {file_path} pages to images...")
        pages = convert_from_path(file_path, first_page=1, last_page=3)
        logger.info(f"Converted {len(pages)} pages.")
        
        # Initialize Gemini Model
        llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GOOGLE_API_KEY,
            temperature=0.0
        )
        
        raw_text_list = []
        extracted_txs = []
        
        for idx, page in enumerate(pages):
            # Save temporary image
            temp_img_path = f"{file_path}_page_{idx+1}.jpg"
            page.save(temp_img_path, "JPEG")
            
            try:
                base64_img = encode_image(temp_img_path)
                
                # Call Gemini with visual prompt
                prompt = (
                    "You are an expert financial auditor. Analyze this receipt or invoice page. "
                    "Extract the following details as a valid JSON object. "
                    "Strictly return ONLY the raw JSON object, without markdown formatting or code blocks. "
                    "Fields: "
                    "{\n"
                    "  \"merchant\": \"name of the merchant or vendor (string, or null)\",\n"
                    "  \"transaction_date\": \"date in YYYY-MM-DD format (string, or null)\",\n"
                    "  \"total_amount\": \"total amount as a float number (number, or null)\",\n"
                    "  \"line_items\": [\"list of individual line item descriptions and prices if visible (array of strings)\"],\n"
                    "  \"category\": \"inferred expense category like software, meals, travel, etc. (string, or null)\",\n"
                    "  \"confidence_score\": \"confidence score between 0.0 and 1.0 (number)\",\n"
                    "  \"raw_text\": \"full text content read from the page (string)\"\n"
                    "}"
                )
                
                logger.info(f"Sending page {idx+1} to Gemini Vision...")
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
                response_text = response.content
                
                # Clean code blocks from markdown responses if model returns it
                if "```json" in response_text:
                    response_text = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[1].split("```")[0].strip()
                else:
                    response_text = response_text.strip()
                    
                data = json.loads(response_text)
                
                # Store text
                raw_text_list.append(data.get("raw_text", ""))
                
                # Build extracted transaction object
                extracted_txs.append({
                    "merchant": data.get("merchant"),
                    "transaction_date": data.get("transaction_date"),
                    "total_amount": data.get("total_amount"),
                    "line_items": data.get("line_items", []),
                    "category": data.get("category"),
                    "confidence_score": data.get("confidence_score", 0.8),
                    "ingestion_method": "vision",
                    "page_number": idx + 1
                })
            finally:
                # Cleanup temp image
                if os.path.exists(temp_img_path):
                    os.remove(temp_img_path)
                    
        return {
            "raw_text": "\n\n".join(raw_text_list),
            "extracted_transactions": extracted_txs,
            "ingestion_method": "vision"
        }
    except Exception as e:
        logger.error(f"Error parsing scanned PDF with Gemini Vision: {e}")
        raise e
