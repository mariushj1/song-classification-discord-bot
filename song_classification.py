import requests
import os
from dotenv import load_dotenv
import re
import lyricsgenius
import pandas as pd
from collections import Counter

# Load environment variables from .env file
load_dotenv()

# Define the youtube link and id
yt_url = "https://www.youtube.com/watch?v=RBumgq5yVrA"
yt_id = re.search(r"(?:v=)([a-zA-Z0-9_-]{11})", yt_url)
yt_id = yt_id.group(1)

# Get the YouTube API key from environment variables
yt_api_key = os.getenv("YOUTUBE_API_KEY")

# YouTube Data API endpoint for video details
google_api_url = "https://www.googleapis.com/youtube/v3/videos"

# Set up parameters for the API request
params = {
    "part": "snippet,statistics",
    "id": yt_id,
    "key": yt_api_key,
}

# Send the request
response = requests.get(google_api_url, params=params)

# Check if the request was successful
if response.status_code == 200:
    video_data = response.json()
    if video_data["items"]:
        yt_title = video_data["items"][0]["snippet"]["title"]
    else:
        print("Video not found.")
else:
    print(f"Error: {response.status_code}")

# Cleans title
clean_yt_title = re.sub(r"\s*\(.*?\)", "", yt_title)
clean_yt_title = re.sub(r"ft.*$", "", clean_yt_title).strip()
clean_yt_title = re.sub(r"\[[^\]]*\]", "", clean_yt_title).strip()

# Find the lyrics for the song using the Genius API
genius_client_token = os.getenv("GENIUS_ACCESS_TOKEN")
genius = lyricsgenius.Genius(genius_client_token)
genius.timeout = 30
song_obj = genius.search_song(clean_yt_title)

if song_obj:
    lyrics = song_obj.lyrics
else:
    print("Lyrics not found.")

# Cleaning the lyrics
match = re.search(r'\[Verse 1\](.*)', lyrics, re.DOTALL)
if match:
    cleaned_lyrics = match.group(1).strip()
else:
    cleaned_lyrics = lyrics  # fallback

cleaned_lyrics = re.sub(r'\[.*?\]\s*', '', cleaned_lyrics)
cleaned_lyrics = cleaned_lyrics.replace("'", "")

# Using NLP to determine lyrics sentiment
cleaned_lyrics = cleaned_lyrics.lower()

words = re.findall(r'\b\w+\b', cleaned_lyrics)
word_counts = Counter(words)
df = pd.DataFrame(word_counts.items(), columns=['word', 'count'])
df = df.sort_values(by='count', ascending=False).reset_index(drop=True)
print(df)
