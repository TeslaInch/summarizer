# llm/fallback.py
from .gemini import summarize_with_gemini
from .fireworks import summarize_with_fireworks  # Make sure this file exists
from .groq import summarize_with_groq
import asyncio
import logging

logger = logging.getLogger(__name__)

# Blocklist: phrases that indicate invalid input
INVALID_INPUT_PATTERNS = {
    "scanned", "not supported", "no readable text", "too short", "corrupted",
    "error", "failed", "limit", "key", "unavailable", "timeout", "exceeded",
    "invalid", "gemini", "groq", "429", "500", "could not generate"
}

def is_invalid_input(text: str) -> bool:
    if not text or len(text.strip()) < 10:
        return True
    text_lower = text.lower()
    return any(pattern in text_lower for pattern in INVALID_INPUT_PATTERNS)

def get_summary_prompt(text: str) -> str:
    word_count = len(text.split())
    target_length = max(5, min(3690, int(word_count * 0.36)))  # 36%, cap at 3690
    return f"""
Please generate a clear and concise summary of the following text.
Focus on the main ideas, key points, and essential conclusions.

Target length: {target_length} words.
Do not use markdown. Use plain text only.

Text to summarize:
{text.strip()}
"""

async def generate_summary(text: str) -> str:
    # ✅ 1. Validate input BEFORE creating any prompt
    if is_invalid_input(text):
        logger.warning("Invalid input blocked: %s", text[:100])
        return "Summary could not be generated. The content may be invalid or unsupported."

    # ✅ 2. Try Gemini first
    try:
        gemini_prompt = get_summary_prompt(text)
        result = await summarize_with_gemini(gemini_prompt)
        if result and len(result.strip()) > 50 and "error" not in result.lower():
            logger.info("✅ Success with Gemini")
            return result
    except Exception as e:
        logger.error(f"❌ Gemini failed: {e}")

    # ✅ 3. Try Fireworks (second choice)
    try:
        fireworks_prompt = get_summary_prompt(text)
        result = await summarize_with_fireworks(fireworks_prompt)
        if result and len(result.strip()) > 50 and "error" not in result.lower():
            logger.info("✅ Success with Fireworks")
            return result
    except Exception as e:
        logger.error(f"❌ Fireworks failed: {e}")

    # ✅ 4. Try Groq (final fallback)
    try:
        groq_prompt = get_summary_prompt(text)
        result = await summarize_with_groq(groq_prompt)
        if result and len(result.strip()) > 50 and "error" not in result.lower():
            logger.info("✅ Success with Groq")
            return result
    except Exception as e:
        logger.error(f"❌ Groq failed: {e}")

    # ✅ 5. All providers failed
    return "Summary could not be generated. Please try again later."