import os
import io
import re
import json
import logging
from collections import Counter
from datetime import datetime
import httpx

import streamlit as st
from dotenv import load_dotenv
from supabase import create_client, Client

from utils.pdf_utils import extract_text_from_pdf
from utils.youtube_utils import get_youtube_videos

# -----------------------------
# Logging setup
# -----------------------------
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# -----------------------------
# Basic setup
# -----------------------------
st.set_page_config(page_title="PDF → Summary + Videos", page_icon="📚", layout="centered")
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUMMARIZER_API_URL = os.getenv("SUMMARIZER_API_URL")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

if not (SUPABASE_URL and SUPABASE_KEY and SUMMARIZER_API_URL and YOUTUBE_API_KEY):
    st.error("⚠️ Configuration error: Some environment variables are missing. Please check your `.env` file.")
    st.stop()

def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# Session persistence helpers
# -----------------------------
SESSION_FILE = ".supabase_session.json"

def save_session(session):
    """Save session to a local JSON file."""
    try:
        with open(SESSION_FILE, "w") as f:
            json.dump({
                "access_token": session.access_token,
                "refresh_token": session.refresh_token
            }, f)
    except Exception as e:
        logger.error(f"Failed to save session: {e}")

def restore_session(client: Client):
    """Restore a session from local file if valid."""
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, "r") as f:
            data = json.load(f)
        res = client.auth.set_session(data["access_token"], data["refresh_token"])
        if res and res.user:
            st.session_state["access_token"] = res.session.access_token
            st.session_state["user"] = {
                "id": res.user.id,
                "email": res.user.email,
            }
            return res
    except Exception as e:
        logger.error(f"Failed to restore session: {e}")
    return None

def clear_session():
    """Clear session data locally and in session_state."""
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)
    st.session_state.clear()

# -----------------------------
# Utilities
# -----------------------------
STOPWORDS = set("""
a an and are as at be but by for if in into is it no not of on or such that the their then there these they this to was will with from
you your we our can could should would may might about over under between among across within without into onto than
i me my mine he she him her his hers its it's them they theirs us we ours who whom which what when where how why
pdf text page pages doc docs document study course topic lecture lesson exam exam(s) note notes
""".split())

def extract_keywords(text: str, k: int = 6):
    tokens = re.findall(r"[A-Za-z][A-Za-z\-]+", text.lower())
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 2]
    freq = Counter(tokens)
    return [w for w, _ in freq.most_common(k)]

def ensure_bucket(client: Client, bucket_name: str = "pdfs"):
    try:
        client.storage.get_bucket(bucket_name)
    except Exception:
        try:
            client.storage.create_bucket(bucket_name, public=False)
        except Exception as e:
            logger.error(f"Failed to ensure bucket '{bucket_name}': {e}")

def save_summary_row(client: Client, user_id: str, filename: str, summary: str):
    try:
        client.table("summaries").insert({
            "user_id": user_id,
            "filename": filename,
            "summary": summary,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        logger.error(f"Failed to save summary row: {e}")

def upload_pdf_bytes(client: Client, user_id: str, filename: str, data: bytes, bucket_name: str = "pdfs") -> str:
    ensure_bucket(client, bucket_name)
    path = f"{user_id}/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
    try:
        client.storage.from_(bucket_name).upload(path=path, file=data)
    except Exception as e:
        logger.error(f"Failed to upload PDF to storage: {e}")
    return path

# -----------------------------
# Auth UI
# -----------------------------
def auth_ui(client: Client):
    st.title("📚 PDF Summarizer + YouTube")
    st.caption("Sign up or log in to continue")

    tabs = st.tabs(["🔐 Log in", "🆕 Sign up"])

    # --- Login ---
    with tabs[0]:
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Log in")
            if submitted:
                try:
                    res = client.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state["access_token"] = res.session.access_token
                    st.session_state["user"] = {
                        "id": res.user.id,
                        "email": res.user.email,
                    }
                    save_session(res.session)
                    st.success("✅ Logged in successfully!")
                    st.rerun()
                except Exception:
                    logger.error("Login failed", exc_info=True)
                    st.error("❌ Login failed. Please check your credentials and try again.")

    # --- Signup ---
    with tabs[1]:
        with st.form("signup_form"):
            email = st.text_input("Email", key="signup_email")
            password = st.text_input("Password (min 6 chars)", type="password", key="signup_password")
            submitted = st.form_submit_button("Create account")
            if submitted:
                try:
                    client.auth.sign_up({"email": email, "password": password})
                    st.success("✅ Signup successful! Please verify your email, then log in.")
                except Exception:
                    logger.error("Signup failed", exc_info=True)
                    st.error("❌ Signup failed. Please try again later.")

# -----------------------------
# Main App
# -----------------------------
def app_ui(client: Client):
    user = st.session_state.get("user")
    st.sidebar.write(f"Signed in as: **{user.get('email', '')}**")
    if st.sidebar.button("Log out"):
        clear_session()
        st.rerun()

    st.title("📄 → ✂️ → ▶️ Summarize & Watch")
    st.caption("Upload a PDF, get a quick summary, and watch related YouTube videos right here.")

    uploaded = st.file_uploader("Upload a PDF", type=["pdf"])
    if uploaded is None:
        st.info("📤 Drop a PDF above to get started.")
        return

    data = uploaded.getvalue()
    file_for_text = io.BytesIO(data)

    # --- Extract text ---
    with st.spinner("🔍 Extracting text from your PDF..."):
        try:
            full_text = extract_text_from_pdf(file_for_text)
        except Exception:
            logger.error("PDF extraction failed", exc_info=True)
            st.error("❌ Sorry, we couldn't read your PDF. Please try another file.")
            return

    if full_text:
        preview_text = full_text[:1000]
        st.subheader("🔍 Extracted Text Preview")
        st.text_area("Preview", preview_text, height=200)
    else:
        st.warning("⚠️ Could not extract enough text from the PDF.")
        return

    # --- Summarize ---
    st.subheader("📝 Summary")
    summary = ""
    with st.spinner("✂️ Summarizing your document..."):
        try:
            with httpx.stream("POST", f"{SUMMARIZER_API_URL}/summarize", json={"text": full_text}, timeout=None) as r:
                r.raise_for_status()
                summary_box = st.empty()
                partial_summary = ""
                for line in r.iter_text():
                    if line.strip():
                        partial_summary += line + "\n\n"
                        summary_box.write(partial_summary)
                summary = partial_summary.strip()
        except Exception:
            logger.error("Summarization failed", exc_info=True)
            st.error("❌ Sorry, we couldn't summarize your PDF at the moment. Please try again later.")
            return

    # --- Save file info ---
    try:
        path = upload_pdf_bytes(client, user["id"], uploaded.name, data)
        save_summary_row(client, user["id"], uploaded.name, summary)
        with st.expander("ℹ️ Storage Info"):
            st.caption(f"Stored at: `{path}` in bucket `pdfs`")
    except Exception:
        logger.error("Failed to save file/summary", exc_info=True)

    # --- YouTube videos ---
    keywords = extract_keywords(summary or full_text, k=6)
    query = " ".join(keywords) if keywords else "lecture introduction overview"
    st.subheader("🎥 Related Videos")
    try:
        videos = get_youtube_videos(query, max_results=3)
        if not videos:
            st.info("ℹ️ No related videos found. Try another document.")
        else:
            for vid in videos:
                st.write(vid["title"])
                st.video(f"https://www.youtube.com/watch?v={vid['id']}")
    except Exception:
        logger.error("Failed to fetch YouTube videos", exc_info=True)
        st.error("❌ Could not load related videos at this time.")

# -----------------------------
# Entry
# -----------------------------
def main():
    client = get_supabase()
    if "user" not in st.session_state:
        restore_session(client)

    if "user" not in st.session_state:
        auth_ui(client)
    else:
        app_ui(client)

if __name__ == "__main__":
    main()
