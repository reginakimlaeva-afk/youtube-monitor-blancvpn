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
    # сюда потом вставим каналы
]

SEEN_FILE = "seen_videos.txt"


def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r") as f:
        return set(line.strip() for line in f.readlines())


def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        for vid in seen:
            f.write(vid + "\n")


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": False
    }
    requests.post(url, data=data)


def get_videos(channel_id):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": YOUTUBE_API_KEY,
        "channelId": channel_id,
        "part": "snippet",
        "order": "date",
        "maxResults": 50
    }

    videos = []
    while True:
        res = requests.get(url, params=params).json()

        for item in res.get("items", []):
            if item["id"]["kind"] == "youtube#video":
                videos.append(item["id"]["videoId"])

        if "nextPageToken" in res:
            params["pageToken"] = res["nextPageToken"]
        else:
            break

        if len(videos) >= 200:
            break

    return videos


def get_video_details(video_ids):
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "key": YOUTUBE_API_KEY,
        "id": ",".join(video_ids),
        "part": "snippet"
    }

    res = requests.get(url, params=params).json()
    return res.get("items", [])


def check_video(video):
    description = video["snippet"].get("description", "")

    for kw in KEYWORDS:
        if kw in description:
            return True

    return False


def main():
    seen = load_seen()
    new_seen = set(seen)

    first_run = len(seen) == 0

    for channel_id in CHANNEL_IDS:
        video_ids = get_videos(channel_id)

        for i in range(0, len(video_ids), 50):
            chunk = video_ids[i:i+50]
            videos = get_video_details(chunk)

            for video in videos:
                vid = video["id"]

                if vid in seen:
                    continue

                if check_video(video):
                    if not first_run:
                        title = video["snippet"]["title"]
                        url = f"https://www.youtube.com/watch?v={vid}"
                        text = f"{title}\n{url}"
                        send_telegram(text)

                new_seen.add(vid)

    save_seen(new_seen)


if __name__ == "__main__":
    main()
