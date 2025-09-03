# utils/youtube_utils.py
import httpx
import os
import re
from typing import List, Dict, Any
from llm.fallback import generate_summary as llm_generate_summary

# YouTube API Config
API_KEY = os.getenv("YOUTUBE_API_KEY")
BASE_URL = "https://www.googleapis.com/youtube/v3/search"

# Trusted educational channels (Tier 1 - highest quality)
TRUSTED_CHANNELS = {
    "3blue1brown", "statquest", "crashcourse", "khanacademy", "andrew ng",
    "veritasium", "ted-ed", "numberphile", "deepmind", "sentdex",
    "machinelearningmemo", "freecodecamp", "mit", "stanford", "harvard",
    "aws", "googlecloud", "nasa", "ted", "tedtalks", "pewresearch"
}

# Quality general education (Tier 2 - acceptable if Tier 1 fails)
QUALITY_CHANNELS = {
    "vox", "pbs", "reallifelore", "upandatom", "two minute papers",
    "smartereveryday", "derekholt", "huxli", "aaron", "ted",
    "kurzgesagt", "vsauce", "physicsgirl", "minutephysics"
}

# Blocklist: clickbait, low-quality, spam
BLOCKED_WORDS = {
    "meme", "funny", "top 10", "compilation", "prank", "viral",
    "challenge", "try not to laugh", "satisfying", "cute animals",
    "fun", "entertainment", "music", "dance", "comedy", "reaction"
}

def get_channel_tier(channel_name: str) -> int:
    """Return 1 (trusted), 2 (quality), or 3 (unknown)"""
    name = channel_name.lower()
    if any(trusted in name for trusted in TRUSTED_CHANNELS):
        return 1
    if any(quality in name for quality in QUALITY_CHANNELS):
        return 2
    return 3

def is_blocked_title(title: str) -> bool:
    """Return True if title contains blocked keywords"""
    title_lower = title.lower()
    return any(word in title_lower for word in BLOCKED_WORDS)

async def generate_search_queries(summary: str, max_queries: int = 2) -> list:
    """
    Generate YouTube search queries from a summary.
    1. Try LLM to generate natural, searchable queries
    2. If that fails, fall back to 'main phrase + tutorial/explained'
    3. Return empty list if no valid queries
    """
    if not summary or len(summary.strip()) < 10:
        return []

    # Step 1: Use LLM to generate natural search queries
    try:
        prompt = f"""
        Based on the following text, generate up to {max_queries} concise and realistic YouTube search queries.
        Focus on beginner-friendly, educational phrases that people actually type.

        Do not use markdown or numbering.
        Return one query per line.

        Text:
        {summary.strip()}
        """
        response = await llm_generate_summary(prompt)
        if not response:
            raise Exception("No response from LLM")

        queries = []
        for line in response.split('\n'):
            line = line.strip()
            # Skip empty, numbered, or too short lines
            if not line or len(line) < 5 or line[0].isdigit() or line.startswith(('-', '*')):
                continue
            queries.append(line)
            if len(queries) >= max_queries:
                break

        if queries:
            return queries
    except Exception as e:
        print(f"LLM query generation failed: {e}")

    # Step 2: Fallback — extract main phrase and add 'tutorial' or 'explained'
    try:
        words = summary.strip().split()
        if len(words) == 0:
            return []

        # Take first 3–5 meaningful words
        key_phrase = ' '.join([w.strip('.,:;()') for w in words[:5]])
        if len(key_phrase) > 10:
            return [
                f"{key_phrase} tutorial",
                f"{key_phrase} explained"
            ][:max_queries]
    except Exception as e:
        print(f"Fallback query generation failed: {e}")

    # No valid queries
    return []

def sanitize_query(query: str) -> str:
    """Remove invalid characters from query"""
    query = re.sub(r'[^\w\s\-:&]', '', query)
    return query.strip()

async def recommend_videos_from_summary(summary: str, min_tier1: int = 2) -> List[Dict[str, Any]]:
    """
    Recommend high-quality YouTube videos based on a summary.
    Uses LLM to generate smart queries and applies tiered filtering.
    Returns empty list if summary is invalid.
    """
    # ✅ Skip if summary failed
    if not summary or any(phrase in summary.lower() for phrase in [
        "could not generate", "try again", "high demand", "summary could not be finalized"
    ]):
        return []

    try:
        queries = await generate_search_queries(summary)
        if not queries:
            return []

        all_videos = []
        seen_video_ids = set()

        for query in queries:
            sanitized_query = sanitize_query(query)
            if not sanitized_query:
                continue

            params = {
                "part": "snippet",
                "q": sanitized_query,
                "key": API_KEY,
                "maxResults": 10,
                "type": "video",
                "order": "rating"  # Prioritize quality over views
            }

            try:
                response = httpx.get(BASE_URL, params=params, timeout=15.0)
                response.raise_for_status()
                data = response.json()
            except Exception as e:
                print(f"Error fetching YouTube results for '{query}': {e}")
                continue

            for item in data.get("items", []):
                try:
                    video_id = item["id"]["videoId"]
                    snippet = item["snippet"]
                    title = snippet.get("title", "")
                    channel = snippet.get("channelTitle", "")

                    if not title or not channel:
                        continue

                    if video_id in seen_video_ids or is_blocked_title(title):
                        continue

                    # Add video with tier info
                    tier = get_channel_tier(channel)
                    all_videos.append({
                        "id": video_id,
                        "title": title,
                        "channel": channel,
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                        "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url",
                            f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"),
                        "duration": "Unknown",
                        "publishedAt": snippet.get("publishedAt", ""),
                        "tier": tier
                    })
                    seen_video_ids.add(video_id)
                except Exception as e:
                    print(f"Error parsing video item: {e}")
                    continue

        # Sort: Tier 1 first, then 2, then 3
        all_videos.sort(key=lambda x: (x["tier"], x["publishedAt"]))

        # Prioritize Tier 1, then fill with Tier 2/3
        final_videos = [v for v in all_videos if v["tier"] == 1]
        remaining = 6 - len(final_videos)
        if remaining > 0:
            final_videos += [v for v in all_videos if v["tier"] == 2][:remaining]
            remaining = 6 - len(final_videos)
        if remaining > 0:
            final_videos += [v for v in all_videos if v["tier"] == 3][:remaining]

        return final_videos[:6]

    except Exception as e:
        print(f"Unexpected error in recommend_videos_from_summary: {e}")
        return []