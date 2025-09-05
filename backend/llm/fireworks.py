# llm/fireworks.py
from openai import AsyncOpenAI
import os
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

api_key = os.getenv("FIREWORKS_API_KEY")
if not api_key:
    logger.warning("FIREWORKS_API_KEY not set")

# Use Fireworks with OpenAI client + 60s timeout
client = AsyncOpenAI(
    base_url="https://api.fireworks.ai/inference/v1",  # ✅ Fixed: removed trailing space
    api_key=api_key,
    timeout=60.0  # ✅ 60-second timeout for all requests
) if api_key else None

async def summarize_with_fireworks(prompt: str, model: str = "accounts/fireworks/models/llama-v3p1-8b-instruct") -> str:
    """
    Generate a summary using Fireworks.ai
    Default model: Llama 3.1 8B Instruct (fast & free tier eligible)
    """
    if not client:
        logger.warning("Fireworks skipped: API key missing")
        return None

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.7,
            top_p=0.9
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Fireworks error: {e}")
        return None