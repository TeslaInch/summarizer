# llm/gemini.py
import google.generativeai as genai
import os
from dotenv import load_dotenv
import asyncio
import logging

load_dotenv()

logger = logging.getLogger(__name__)

api_key = os.getenv("GEMINI_API_KEY3")
if api_key:
    genai.configure(api_key=api_key)
else:
    logger.warning("GEMINI_API_KEY not set")

def _sync_summarize(prompt: str) -> str:
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini sync error: {e}")
        return None

async def summarize_with_gemini3(prompt: str) -> str:
    if not api_key:
        return None
    try:
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(None, _sync_summarize, prompt),
            timeout=60.0
        )
        return result
    except asyncio.TimeoutError:
        logger.warning("Gemini request timed out after 60 seconds")
        return None
    except Exception as e:
        logger.error(f"Gemini async error: {e}")
        return None