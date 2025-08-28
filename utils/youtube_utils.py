import httpx, os

API_KEY = os.getenv("YOUTUBE_API_KEY")

def get_youtube_videos(query, max_results=3):
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&key={API_KEY}&maxResults={max_results}"
    response = httpx.get(url).json()
    videos = [
        {"title": item["snippet"]["title"], "id": item["id"]["videoId"]}
        for item in response["items"] if item["id"]["kind"]=="youtube#video"
    ]
    return videos
