from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
import httpx
import os
import asyncio
from pydantic import BaseModel
from dotenv import load_dotenv
from transformers import BartTokenizer
from concurrent.futures import ProcessPoolExecutor
from supabase_client import supabase
from auth_utils import verify_token
from utils.pdf_utils import extract_text_from_pdf
from fastapi.middleware.cors import CORSMiddleware
from utils.youtube_utils import recommend_videos_from_summary
from typing import Dict, List, Any
import json
import time

load_dotenv()

app = FastAPI()

HF_API_KEY = os.getenv("HF_API_KEY")
MODEL_ID = "facebook/bart-large-cnn"
tokenizer = BartTokenizer.from_pretrained(MODEL_ID)

# Store processed PDFs in memory (use database in production)
processed_pdfs: Dict[str, Dict[str, Any]] = {}

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Helper Functions
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

async def generate_summary_from_text(text: str) -> str:
    """Generate summary from extracted text"""
    chunks = chunk_text_parallel(text, workers=2, max_tokens=1024, min_words=50)
    
    summaries = []
    for chunk in chunks:
        summary = await summarize_chunk(chunk)
        summaries.append(summary)
        await asyncio.sleep(0.1)
    
    # Combine all chunk summaries
    combined_summary = " ".join(summaries)
    
    # If combined summary is too long, summarize it again
    if len(combined_summary.split()) > 200:
        final_summary = await summarize_chunk(combined_summary)
        return final_summary
    
    return combined_summary

# -----------------------------
# Models
# -----------------------------
class SummarizeRequest(BaseModel):
    text: str

class SummaryRequest(BaseModel):
    summary: str

# -----------------------------
# Routes
# -----------------------------
@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload PDF and process it completely - extract text, generate summary, get video recommendations"""
    try:
        content = await file.read()
        print(f"📄 Received file: {file.filename}, size: {len(content)} bytes")

        # Extract text from PDF
        text = extract_text_from_pdf(content)
        if not text.strip():
            return JSONResponse({"error": "No readable text found in PDF"}, status_code=400)

        # Store initial data
        pdf_data = {
            "filename": file.filename,
            "extracted_text": text,
            "upload_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "processing_status": "processing",
            "summary": "",
            "videos": []
        }
        processed_pdfs[file.filename] = pdf_data

        # Background processing - generate summary and get videos
        asyncio.create_task(process_pdf_background(file.filename, text))

        return {
            "message": "PDF uploaded successfully", 
            "filename": file.filename,
            "status": "processing"
        }
    except Exception as e:
        import traceback
        print("🚨 Error while processing PDF:")
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)

async def process_pdf_background(filename: str, text: str):
    """Background task to process PDF - generate summary and get video recommendations"""
    try:
        # Generate summary
        summary = await generate_summary_from_text(text)
        
        # Get video recommendations
        videos = recommend_videos_from_summary(summary)
        
        # Update stored data
        if filename in processed_pdfs:
            processed_pdfs[filename].update({
                "summary": summary,
                "videos": videos,
                "processing_status": "completed"
            })
            print(f"✅ Completed processing for {filename}")
    except Exception as e:
        print(f"❌ Error processing {filename}: {e}")
        if filename in processed_pdfs:
            processed_pdfs[filename].update({
                "processing_status": "error",
                "error": str(e)
            })

@app.get("/summaries")
async def get_summaries(pdf: str = None):
    """Get summary and video data for a specific PDF or all PDFs"""
    try:
        if pdf:
            # Get specific PDF data
            if pdf not in processed_pdfs:
                raise HTTPException(status_code=404, detail="PDF not found")
            
            pdf_data = processed_pdfs[pdf]
            return {
                "summary": pdf_data.get("summary", ""),
                "videos": pdf_data.get("videos", []),
                "status": pdf_data.get("processing_status", "processing"),
                "upload_date": pdf_data.get("upload_date", ""),
                "error": pdf_data.get("error", "")
            }
        else:
            # Get all PDFs data
            return {"pdfs": processed_pdfs}
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/summarize")
async def summarize_text(payload: SummarizeRequest):
    """Direct text summarization endpoint (for manual text input)"""
    text = payload.text.strip()
    if not text:
        return JSONResponse({"error": "No text provided"}, status_code=400)

    try:
        summary = await generate_summary_from_text(text)
        return {"summary": summary}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/recommend-videos")
def recommend_videos(data: SummaryRequest):
    """Get video recommendations from summary"""
    try:
        recommendations = recommend_videos_from_summary(data.summary)
        return {"success": True, "data": recommendations}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "API is running"}

@app.post("/protected-route")
def protected_route(user=Depends(verify_token)):
    return {"message": f"Hello, {user['email']}!"}