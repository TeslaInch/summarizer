// src/services/youtubeService.js
export const fetchRecommendedVideos = async (summary) => {
  try {
    const response = await fetch("http://localhost:8000/recommend-videos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ summary }),
    });
    const data = await response.json();
    if (data.success) {
      return data.data; // returns an array of recommended videos
    } else {
      console.error("Video fetch error:", data.error);
      return [];
    }
  } catch (err) {
    console.error("Network error:", err);
    return [];
  }
};
