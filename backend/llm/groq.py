# llm/groq.py
from groq import AsyncGroq
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    logger.warning("GROQ_API_KEY not set")

client = AsyncGroq(api_key=api_key, timeout=60.0) if api_key else None

async def summarize_with_groq(prompt: str) -> str:
    if not client:
        return None
    try:
        chat_completion = await client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",  # ✅ Current stable model
            max_tokens=400,
            temperature=0.7
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Groq error: {e}")
        return None