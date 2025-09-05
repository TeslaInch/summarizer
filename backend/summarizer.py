# test_fireworks.py
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables (so you can use .env)
load_dotenv()

# 🔧 Configuration
FIREWORKS_API_KEY = os.getenv("FIREWORKS_API_KEY")
MODEL = "accounts/fireworks/models/llama-v3p1-8b-instruct"
PROMPT = "Hello! Test if Fireworks API is working. Reply with 'Yes, I'm alive!'"

if not FIREWORKS_API_KEY:
    print("❌ Error: FIREWORKS_API_KEY not found in .env")
    exit(1)

print("🚀 Testing Fireworks.ai API...\n")
print(f"Using model: {MODEL}\n")

try:
    # Create client pointing to Fireworks
    client = OpenAI(
        base_url="https://api.fireworks.ai/inference/v1",
        api_key=FIREWORKS_API_KEY
    )

    # Make the request
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": PROMPT}
        ],
        max_tokens=100,
        temperature=0.7
    )

    # Print result
    content = response.choices[0].message.content.strip()
    print("✅ Success! Fireworks API is working.\n")
    print("💬 Response:")
    print(content)

except Exception as e:
    print("❌ Failed to connect to Fireworks API\n")
    print(f"Error: {type(e).__name__}: {str(e)}")
    if "authentication" in str(e).lower():
        print("💡 Hint: Check if your FIREWORKS_API_KEY is correct")
    elif "rate limit" in str(e).lower():
        print("💡 Hint: You might be rate-limited (unlikely on free tier)")
    elif "model" in str(e).lower():
        print("💡 Hint: Model ID might be invalid")