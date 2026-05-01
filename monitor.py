import os
import requests
from datetime import datetime, timedelta

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

KEYWORDS = [
    "BlancVPN",
    "https://blanc.link/"
]

CHANNEL_IDS = [
    "UCLxr1ACVGlrUvpGkc_ruMKg",
    "UCuaYG7fdQ-4myL_CVtvwNHQ",
    "UC71duAY6rjGEhGQAiytiFPw",
    "UCUS6gJ_FCzLS5w2InH6oYmA",
    "UCpJuziZAwEFnoeNGSaxQlCQ",
    "UC30guDBHUu_3j-uZdlfo9TQ",
    "UCR-Hcwi27-Ee6VnGzmxE1pA",
    "UCgpSieplNxXxLXYAzJLLpng",
    "UC101o-vQ2iOj9vr00JUlyKw",
    "UCL1rJ0ROIw9V1qFeIN0ZTZQ",
    "UCe5_WsZ_7RM14t3MImLWNZg",
    "UCZy0mCOt6izb2o1bQEUNGRg",
    "UCM7-8EfoIv0T9cCI4FhHbKQ",
    "UCUGfDbfRIx51kJGGHIFo8Rw",
    "UCMCgOm8GZkHp8zJ6l7_hIuA"
]

SEEN_FILE = "seen_videos.txt"


def load_seen():
    try:
        with open(SEEN_FILE, "r") as f:
            return set(f.read().splitlines())
    except:
        return set()


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        f.write("\n".join(seen))


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": text})


def get_recent_videos(channel_id):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": YOUTUBE_API_KEY,
        "channelId": channel_id,
        "part": "snippet",
        "order": "date",
        "maxResults": 5
    }
    return requests.get(url, params=params).json().get("items", [])


def check_keywords(text):
    text = text.lower()
    return any(k.lower() in text for k in KEYWORDS)


def main():
    seen = load_seen()
    new_seen = set(seen)

    for channel_id in CHANNEL_IDS:
        videos = get_recent_videos(channel_id)

        for v in videos:
            video_id = v["id"].get("videoId")
            if not video_id:
                continue

            if video_id in seen:
                continue

            title = v["snippet"]["title"]
            description = v["snippet"]["description"]

            if check_keywords(title) or check_keywords(description):
                link = f"https://youtube.com/watch?v={video_id}"
                send_telegram(f"Найдено упоминание:\n{title}\n{link}")

            new_seen.add(video_id)

    save_seen(new_seen)


if __name__ == "__main__":
    main()
