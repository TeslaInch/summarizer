import httpx
import os
from rake_nltk import Rake

API_KEY = os.getenv("YOUTUBE_API_KEY")
BASE_URL = "https://www.googleapis.com/youtube/v3/search"

def extract_keywords(summary: str, max_keywords: int = 3):
    """
    Extract key phrases from the summary text.
    """
    r = Rake()  # uses NLTK stopwords by default
    r.extract_keywords_from_text(summary)
    phrases = r.get_ranked_phrases()
    return phrases[:max_keywords]  # return top keywords


def get_youtube_videos(query: str, max_results: int = 3):
    """
    Fetch YouTube videos by keyword query.
    Returns a clean list with title, url, and thumbnail.
    """
    if not API_KEY:
        raise ValueError("Missing YOUTUBE_API_KEY in environment variables.")

    params = {
        "part": "snippet",
        "q": query,
        "key": API_KEY,
        "maxResults": max_results,
        "type": "video",
        "order": "relevance"
    }

    try:
        response = httpx.get(BASE_URL, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()
    except httpx.HTTPError as e:
        print(f"Error fetching videos: {e}")
        return []

    videos = []
    for item in data.get("items", []):
        video_id = item["id"]["videoId"]
        videos.append({
            "id": video_id,
            "title": item["snippet"]["title"],
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
        })

    return videos


def recommend_videos_from_summary(summary: str, max_keywords: int = 3, max_results: int = 3):
    """
    Extract keywords from the summary, then fetch videos for each keyword.
    """
    keywords = extract_keywords(summary, max_keywords)
    recommendations = {}

    for keyword in keywords:
        recommendations[keyword] = get_youtube_videos(keyword, max_results)

    return recommendations
