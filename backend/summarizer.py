# test_gemini2.py
from llm.gemini2 import summarize_with_gemini2  # Adjust import if needed
import asyncio
import logging

# Set up logging to see output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

async def main():
    print("🚀 Testing Gemini API (using GEMINI_API_KEY2)...\n")

    # Test prompt
    test_prompt = """
    Explain in simple terms how photosynthesis works.
    Keep it under 100 words.
    """

    print(f"📝 Prompt: {test_prompt.strip()}")
    print("\n⏳ Generating summary...\n")

    # Call your function
    summary = await summarize_with_gemini2(test_prompt)

    if summary:
        print("✅ Success! Gemini returned a summary:\n")
        print(f"💬 {summary}")
    else:
        print("❌ Failed to get a summary. Check logs for error.")
        print("💡 Common issues:")
        print("   - Invalid or expired GEMINI_API_KEY2")
        print("   - Network issues")
        print("   - Timeout or blocked content")

if __name__ == "__main__":
    asyncio.run(main())