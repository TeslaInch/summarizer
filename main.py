from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import httpx
import os
import asyncio
from pydantic import BaseModel
from dotenv import load_dotenv
from transformers import BartTokenizer
from concurrent.futures import ProcessPoolExecutor

load_dotenv()

app = FastAPI()

HF_API_KEY = os.getenv("HF_API_KEY")
MODEL_ID = "facebook/bart-large-cnn"
tokenizer = BartTokenizer.from_pretrained(MODEL_ID)

# -----------------------------
# Helpers for chunking
# -----------------------------
def chunk_worker(text_slice, max_tokens=1024, min_words=50):
    words = text_slice.split()
    chunks = []
    i = 0
    while i < len(words):
        j = i + 50
        while j < len(words):
            token_count = len(tokenizer.encode(" ".join(words[i:j]), truncation=False))
            if token_count > max_tokens:
                break
            j += 10
        chunk = " ".join(words[i:j-10])
        if len(chunk.split()) >= min_words:
            chunks.append(chunk)
        i = j - 10
    return chunks

def chunk_text_parallel(text, workers=2, max_tokens=1024, min_words=50):
    words = text.split()
    if len(words) < 50:
        return [text]

    split_size = len(words) // workers or len(words)
    slices = [" ".join(words[i:i + split_size]) for i in range(0, len(words), split_size)]

    all_chunks = []
    with ProcessPoolExecutor(max_workers=workers) as executor:
        results = executor.map(chunk_worker, slices)
        for result in results:
            all_chunks.extend(result)
    return all_chunks

# -----------------------------
# Summarization with retries
# -----------------------------
async def summarize_chunk(chunk, retries=3, delay=2):
    url = f"https://router.huggingface.co/hf-inference/models/{MODEL_ID}"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": chunk, "parameters": {"max_length": 200, "min_length": 50}}

    for attempt in range(1, retries + 1):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                result = response.json()
                if isinstance(result, list) and "summary_text" in result[0]:
                    return result[0]["summary_text"]
                return f"Unexpected response: {result}"
        except Exception as e:
            print(f"[WARN] Attempt {attempt} failed: {e}")
            if attempt < retries:
                await asyncio.sleep(delay)
            else:
                return f"[Error summarizing chunk]: {str(e)}"

# -----------------------------
# Request model
# -----------------------------
class SummarizeRequest(BaseModel):
    text: str

# -----------------------------
# Streaming endpoint
# -----------------------------
@app.post("/summarize")
async def summarize_text(payload: SummarizeRequest):
    text = payload.text.strip()
    if not text:
        return StreamingResponse(iter(["No text provided.\n"]), media_type="text/plain")

    chunks = chunk_text_parallel(text, workers=2, max_tokens=1024, min_words=50)

    async def event_stream():
        for i, chunk in enumerate(chunks, start=1):
            summary = await summarize_chunk(chunk)
            yield f"{summary}\n\n"
            await asyncio.sleep(0.1)  # small delay for smooth streaming

    return StreamingResponse(event_stream(), media_type="text/plain")
