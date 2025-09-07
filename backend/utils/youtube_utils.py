# utils/youtube_utils.py
import httpx
import os
import re
from collections import Counter
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()
# YouTube API Config
API_KEY = os.getenv("YOUTUBE_API_KEY")
BASE_URL = "https://www.googleapis.com/youtube/v3/search"

# Stopwords for keyword extraction
STOPWORDS = set("""
a an and are as at be but by for if in into is it no not of on or such that the their then there these they this to was will with from
you your we our can could should would may might about over under between among across within without into onto than
i me my mine he she him her his hers its it's them they theirs us we ours who whom which what when where how why
pdf text page pages doc docs document study course topic lecture lesson exam exam(s) note notes
""".split())

def extract_keywords(text: str, k: int = 6) -> list:
    """Extract top k keywords using frequency and stopwords."""
    tokens = re.findall(r"[A-Za-z][A-Za-z\-]+", text.lower())
    tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 2]
    freq = Counter(tokens)
    return [word for word, _ in freq.most_common(k)]

def recommend_videos_from_summary(summary: str) -> List[Dict[str, Any]]:
    """
    Recommend YouTube videos using keyword extraction.
    Returns empty list if summary is invalid.
    """
    if not summary or len(summary.strip()) < 50:
        return []

    try:
        # Extract keywords
        keywords = extract_keywords(summary, k=6)
        query = " ".join(keywords) if keywords else "lecture introduction overview"
        search_query = f"{query} tutorial"  # Make it search-friendly

        # YouTube API request
        params = {
            "part": "snippet",
            "q": search_query,
            "key": API_KEY,
            "maxResults": 6,
            "type": "video",
            "order": "relevance"
        }

        response = httpx.get(BASE_URL, params=params, timeout=15.0)
        response.raise_for_status()
        data = response.json()

        videos = []
        seen_video_ids = set()

        for item in data.get("items", []):
            try:
                video_id = item["id"]["videoId"]
                snippet = item["snippet"]
                title = snippet.get("title", "")
                channel = snippet.get("channelTitle", "")

                if not title or not channel or video_id in seen_video_ids:
                    continue

                videos.append({
                    "id": video_id,
                    "title": title,
                    "channel": channel,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url",
                        f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"),
                    "duration": "Unknown",
                    "publishedAt": snippet.get("publishedAt", ""),
                })
                seen_video_ids.add(video_id)
            except Exception as e:
                print(f"Error parsing video: {e}")
                continue

        return videos[:6]

    except Exception as e:
        print(f"YouTube search failed: {e}")
        return []