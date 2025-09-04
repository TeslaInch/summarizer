# PDepth: AI-Powered PDF Summarizer & Video Recommender

📚 Upload a PDF → Get a smart summary + the best educational YouTube videos on the topic.

PDepth helps students, researchers, and lifelong learners **understand complex documents faster** by combining AI summarization with high-quality video recommendations — all in one place.

> **Try it live**: [https://pdepth.xyz](https://pdepth.xyz)

---

## 🚀 Features

- ✅ **Smart PDF Summarization**  
  Uses Gemini and Groq to generate concise, dynamic summaries (20% of input length).
  
- ✅ **YouTube Video Recommendations**  
  Finds high-quality educational videos from trusted channels like 3Blue1Brown, Veritasium, and Khan Academy.

- ✅ **Text-Based PDF Only**  
  Rejects scanned or image-based PDFs with clear feedback.

- ✅ **Rate-Limited & Secure**  
  Protects API usage and prevents abuse with per-user quotas.

- ✅ **Signup and Login Required**  
  Fast, frictionless experience.

- ✅ **Production-Ready Backend**  
  Built with FastAPI, async processing, and fallback LLMs.

---

---

## 🛠️ Tech Stack

| Layer | Technology |
|------|------------|
| Frontend | React + Vite + Tailwind CSS |
| Backend | FastAPI (Python) |
| LLMs | Google Gemini, Groq (Llama-3.1-8b-instant) |
| Video API | YouTube Data API v3 |
| PDF Processing | PyMuPDF (fitz), pikepdf |
| Deployment | Vercel (frontend), Render (backend) |

---

## 🧰 Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/TeslaInch/summarizer.git
cd pdepth
2. Backend Setup
Install Dependencies



cd backend
pip install -r requirements.txt
Environment Variables
Create a .env file in the backend/ folder:

env
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
YOUTUBE_API_KEY=your_youtube_api_key
🔑 Get your keys: 

Gemini: Google AI Studio
Groq: Groq Console
YouTube: Google Cloud Console
Run the Backend

uvicorn main:app --reload
Backend runs at http://localhost:8000

3. Frontend Setup

cd frontend
npm install
npm run dev
Frontend runs at http://localhost:3000

Connect to Backend
In frontend/.env:

env
VITE_API_BASE_URL=http://localhost:8000