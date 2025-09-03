# test_llms.py
import asyncio
import os
import sys

# Add project root to path
sys.path.append(".")

from llm.fallback import generate_summary

async def main():
    sample_text = """
    Artificial intelligence is a wonderful field that enables machines to learn from data.
    It includes machine learning, deep learning, natural language processing, and robotics.
    AI is transforming healthcare, education, finance, and many other industries.
    """

    print("Testing LLM providers...\n")
    result = await generate_summary(sample_text)
    print("\nFinal Summary:\n", result)

if __name__ == "__main__":
    asyncio.run(main())