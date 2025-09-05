# main.py
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
import os
import asyncio
from pydantic import BaseModel
from dotenv import load_dotenv
from utils.pdf_utils import extract_text_from_pdf
from fastapi.middleware.cors import CORSMiddleware
from utils.youtube_utils import recommend_videos_from_summary
from typing import Dict, List, Any, Optional
import time
import logging
from contextlib import asynccontextmanager
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from llm.fallback import generate_summary as llm_generate_summary

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# -----------------------------
# User Quota: 5 PDFs/hour per IP
# -----------------------------
user_pdf_count = {}

def is_allowed_upload(ip: str) -> bool:
    now = time.time()
    if ip not in user_pdf_count:
        user_pdf_count[ip] = {"count": 0, "reset_time": now + 3600}
    elif now > user_pdf_count[ip]["reset_time"]:
        user_pdf_count[ip] = {"count": 0, "reset_time": now + 3600}
    return user_pdf_count[ip]["count"] < 5

def increment_pdf_count(ip: str):
    if ip in user_pdf_count:
        user_pdf_count[ip]["count"] += 1

# -----------------------------
# Lifespan
# -----------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting PDF Processing API...")
    yield
    logger.info("Shutting down...")

app = FastAPI(title="PDF Processing API", lifespan=lifespan)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "https://pdepth.xyz",
        "http://localhost:3000",
        "http://127.0.0.1:8080",
        "https://www.pdepth.xyz",
        "https://pdepth.vercel.app",
        "https://www.pdepth.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# -----------------------------
# Models
# -----------------------------
class SummarizeRequest(BaseModel):
    text: str

class SummaryRequest(BaseModel):
    summary: str

class ProcessingResponse(BaseModel):
    message: str
    filename: str
    summary: str
    videos: List[Dict[str, Any]]
    status: str
    upload_date: str

# -----------------------------
# Smart Chunking
# -----------------------------
def smart_chunk_text(text: str, max_words: int = 3000) -> List[str]:
    import re
    text = re.sub(r'\s+', ' ', text).strip()
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = []
    current_len = 0

    for sentence in sentences:
        word_count = len(sentence.split())
        if current_len + word_count > max_words and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentence]
            current_len = word_count
        else:
            current_chunk.append(sentence)
            current_len += word_count

    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

async def generate_summary_from_text(text: str) -> str:
    if not text.strip():
        return "No content to summarize."

    word_count = len(text.split())
    if word_count < 600:
        prompt = get_summary_prompt(text)
        return await llm_generate_summary(prompt)

    chunks = smart_chunk_text(text, 3000)
    tasks = [llm_generate_summary(get_summary_prompt(chunk)) for chunk in chunks]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    summaries = [r for r in results if isinstance(r, str) and len(r.strip()) > 20]
    if not summaries:
        return "No valid summary could be generated."

    combined = "\n\n---\n\n".join(summaries)
    final_prompt = get_summary_prompt(combined)
    final = await llm_generate_summary(final_prompt)
    return final or "Summary could not be finalized."

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

# -----------------------------
# Routes
# -----------------------------
@app.get("/")
async def root():
    return {"message": "PDF Processing API", "version": "1.0.0"}

@app.post("/upload-pdf", response_model=ProcessingResponse)
@limiter.limit("5/minute")
async def upload_pdf(request: Request, file: UploadFile = File(...)):
    client_ip = request.client.host

    if not is_allowed_upload(client_ip):
        return JSONResponse(
            {"error": "Hourly limit exceeded. Try again later.", "status": "rate_limited"},
            status_code=429
        )

    try:
        content = await file.read()
        if len(content) > 15 * 1024 * 1024:
            return JSONResponse({"error": "File too large", "status": "too_large"}, status_code=413)

        if not content.startswith(b"%PDF"):
            return JSONResponse({"error": "Invalid PDF", "status": "invalid_pdf"}, status_code=400)

        text = extract_text_from_pdf(content)

# ✅ Block all rejection messages
        rejection_phrases = [
            "scanned", "not supported", "no readable text",
            "too short", "document too short", "corrupted"
        ]
        if any(phrase in text.lower() for phrase in rejection_phrases):
            return JSONResponse(
                {"error": text, "status": "invalid_content"},
                status_code=422
            )

        summary = await generate_summary_from_text(text)

        try:
            videos = await recommend_videos_from_summary(summary)
        except Exception as e:
            logger.warning(f"Video recommendation failed: {e}")
            videos = []

        increment_pdf_count(client_ip)

        return {
            "message": "PDF processed successfully",
            "filename": file.filename,
            "summary": summary,
            "videos": videos,
            "status": "completed",
            "upload_date": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return JSONResponse(
            {"error": "Processing failed. Please try again.", "status": "error"},
            status_code=500
        )

@app.post("/summarize")
@limiter.limit("10/minute")
async def summarize_text(request: Request, payload: SummarizeRequest):
    try:
        text = payload.text.strip()
        if not text:
            return JSONResponse({"error": "No text provided"}, status_code=400)
        summary = await generate_summary_from_text(text)
        return {"summary": summary, "status": "completed"}
    except Exception as e:
        logger.error(f"Summarization error: {e}")
        return JSONResponse(
            {"error": "Failed to summarize text."}, status_code=500
        )

@app.post("/recommend-videos")
@limiter.limit("20/minute")
async def recommend_videos(request: Request, data: SummaryRequest):
    try:
        recommendations = recommend_videos_from_summary(data.summary)
        return {"success": True, "data": recommendations, "count": len(recommendations)}
    except Exception as e:
        logger.error(f"Video recommendation failed: {e}")
        return {"success": False, "error": "Could not fetch videos."}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}