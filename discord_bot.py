import discord
import os
import re
import requests
import lyricsgenius
import pandas as pd
from collections import Counter
import nltk
from nltk.corpus import stopwords
from dotenv import load_dotenv

# Setup
nltk.download('stopwords')
load_dotenv()

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
client = discord.Client(intents=intents)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GENIUS_ACCESS_TOKEN = os.getenv("GENIUS_ACCESS_TOKEN")
genius = lyricsgenius.Genius(GENIUS_ACCESS_TOKEN)
genius.timeout = 30

# Defining function to search youtube
def getTopYoutubeVideoLink(query, api_key):
    url = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'part': 'snippet',
        'q': query,
        'type': 'video',
        'maxResults': 1,
        'key': api_key
    }
    response = response.get(url, parameters)
    data = response.json()

    if 'items' in data and data['items']:
        video_id = data['data'][0]['id']['videoId']
        return f"https://youtube.com/watch?v={video_id}"
    else:  
        return None

# Load AFINN data
afinn_data = []
with open("AFINN-111.txt", 'r') as f:
    for line in f:
        word, score = line.strip().split("\t")
        afinn_data.append([word, float(score)])
afinn_df = pd.DataFrame(afinn_data, columns=['word', 'sentiment'])
afinn_df = afinn_df[~afinn_df['word'].isin(['love', 'loved'])]

stop_words = set(stopwords.words('english'))

# Bot token from environment
DISCORD_TOKEN = os.getenv("DISCORD_CLIENT_SECRET")

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("!judge"):
        content = message.content[len("!judge"):].strip()
        yt_url_match = re.search(r"https://www\.youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})", content)
        
        if yt_url_match:
            print(f"Found YouTube URL: {yt_url_match.group(0)}")  # Debug print for YouTube URL match
            await message.channel.send("listening to the song...")
            yt_id = yt_url_match.group(1)

            # YouTube API request
            params = {
                "part": "snippet",
                "id": yt_id,
                "key": YOUTUBE_API_KEY,
            }
            response = requests.get("https://www.googleapis.com/youtube/v3/videos", params=params)
            
            if response.status_code != 200 or not response.json().get("items"):
                print(f"Failed to retrieve YouTube video info. Response: {response.status_code}")
                await message.channel.send("Couldn't retrieve video info.")
                return

            yt_title = response.json()["items"][0]["snippet"]["title"]
            print(f"Song Title from YouTube: {yt_title}")

            clean_title = re.sub(r"\s*\(.*?\)|ft.*$|\[[^\]]*\]", "", yt_title).strip()
            print(f"Cleaned Song Title: {clean_title}")

            # Genius API search
            song = genius.search_song(clean_title)
            if not song:
                print(f"Lyrics not found for: {clean_title}")
                await message.channel.send("Lyrics not found 😕")
                return

            lyrics = re.sub(r'\[.*?\]\s*', '', song.lyrics).lower()
            lyrics = lyrics.replace("'", "")
            words = re.findall(r'\b\w+\b', lyrics)
            words = [word for word in words if word not in stop_words]
            word_counts = Counter(words)
            word_df = pd.DataFrame(word_counts.items(), columns=['word', 'count'])

            merged_df = pd.merge(word_df, afinn_df, on='word', how='left')
            merged_df['sentiment'] = merged_df['sentiment'].fillna(0)
            merged_df['total_sentiment'] = merged_df['count'] * merged_df['sentiment']

            total_sentiment = merged_df['total_sentiment'].sum()
            print(f"Total Sentiment Score: {total_sentiment}")

            mood = "happy :)" if total_sentiment > 25 else "sad :("
            print(f"Sentiment Mood: {mood}")

            await message.channel.send(f"the song {clean_title} seems to be: **{mood}**")

client.run(DISCORD_TOKEN)