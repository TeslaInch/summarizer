# llm/fallback.py
from .gemini import summarize_with_gemini
from .gemini2 import summarize_with_gemini2
from .gemini3 import summarize_with_gemini3
from .fireworks import summarize_with_fireworks
from .groq import summarize_with_groq
import logging

logger = logging.getLogger(__name__)

# Blocklist: phrases that indicate invalid output (like the prompt itself)
INVALID_OUTPUT_PATTERNS = {
    "please generate", "focus on the main ideas", "target length",
    "do not use markdown", "text to summarize", "based on the following text",
    "concise summary", "key points", "essential conclusions"
}

def is_invalid_output(text: str) -> bool:
    if not text or len(text.strip()) < 50:
        return True
    text_lower = text.lower()
    return any(pattern in text_lower for pattern in INVALID_OUTPUT_PATTERNS)

def get_summary_prompt(text: str) -> str:
    word_count = len(text.split())
    target_length = max(5, min(3690, int(word_count * 0.36)))
    return f"""
Please generate a clear and concise summary of the following text.
Focus on the main ideas, key points, and essential conclusions.

Target length: {target_length} words.
Do not use markdown. Use plain text only.

Text to summarize:
{text.strip()}
"""

async def generate_summary(text: str) -> str:
    if not text or len(text.strip()) < 10:
        return "No content to summarize."

    prompt = get_summary_prompt(text)

    providers = [
        ("Gemini", lambda: summarize_with_gemini(prompt)),
        ("Gemini2", lambda: summarize_with_gemini2(prompt)),
        ("Gemini3", lambda: summarize_with_gemini3(prompt)),
        ("Fireworks", lambda: summarize_with_fireworks(prompt)),
        ("Groq", lambda: summarize_with_groq(prompt)),
    ]

    for name, provider in providers:
        try:
            logger.info(f"Trying {name}...")
            result = await provider()
            if result and not is_invalid_output(result):
                logger.info(f"✅ Success with {name}")
                return result.strip()
        except Exception as e:
            logger.error(f"❌ {name} failed: {e}")
            continue

    # ✅ Only return this if all providers failed
    return "Summary could not be generated. Please try again later."