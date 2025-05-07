import requests
import os
from dotenv import load_dotenv
import re
import lyricsgenius
import pandas as pd
from collections import Counter
import nltk
from nltk.corpus import stopwords

# Load environment variables from .env file
load_dotenv()

# Define the youtube link and id
yt_url = "https://www.youtube.com/watch?v=Kua2dDhqzZw"
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
cleaned_lyrics = cleaned_lyrics.lower()

# Tokenize lyrics
words = re.findall(r'\b\w+\b', cleaned_lyrics)
word_counts = Counter(words)
word_df = pd.DataFrame(word_counts.items(), columns=['word', 'count'])
word_df = word_df.sort_values(by='count', ascending=False).reset_index(drop=True)

# Importing and remove stop word
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))
word_df = word_df[~word_df['word'].isin(stop_words)]

# Getting AFINN sentiment lexicon
file_path = "AFINN-111.txt"
afinn_data = []

with open(file_path, 'r') as f:
    for line in f:
        word, score = line.strip().split("\t") 
        afinn_data.append([word, float(score)]) 

afinn_df = pd.DataFrame(afinn_data, columns=['word', 'sentiment'])
# Manually edit words
afinn_df = afinn_df[~afinn_df['word'].isin(['love', 'loved'])]

# Joining on lyrics df to get word sentiment
merged_df = pd.merge(word_df, afinn_df, on='word', how='left')
merged_df['total_sentiment'] = merged_df['count'] * merged_df['sentiment']

pd.set_option('display.max_rows', None)
print(merged_df)
pd.reset_option('display.max_rows')

total_sentiment = merged_df['total_sentiment'].sum()
if total_sentiment > 25:
    result = "happy :)"
else:
    result = "sad :(",

print(f"Estimated song sentiment: {total_sentiment}")
print(f"The song seems to be: {result}")