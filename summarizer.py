import os
import requests
from dotenv import load_dotenv

load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")
API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}"}

def summarize_text(text: str, max_length=200, min_length=50) -> str:
    payload = {
        "inputs": text,
        "parameters": {"min_length": min_length, "max_length": max_length},
    }
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    if response.status_code != 200:
        raise ValueError(f"Error: {response.status_code} - {response.text}")
    return response.json()[0]["summary_text"]
