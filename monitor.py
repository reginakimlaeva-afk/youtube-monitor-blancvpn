import os
import time
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

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
MODE_FILE = "monitor_mode.txt"

DEEP_LIMIT_PER_CHANNEL = 200
DAILY_LIMIT_PER_CHANNEL = 20
TELEGRAM_DELAY_SECONDS = 2


def load_seen():
    if not os.path.exists(SEEN_FILE):
        return set()

    with open(SEEN_FILE, "r", encoding="utf-8") as file:
        return set(line.strip() for line in file if line.strip())


def save_seen(seen):
    with open(SEEN_FILE, "w", encoding="utf-8") as file:
        for video_id in sorted(seen):
            file.write(video_id + "\n")


def is_deep_mode():
    if not os.path.exists(MODE_FILE):
        return True

    with open(MODE_FILE, "r", encoding="utf-8") as file:
        return file.read().strip() != "daily"


def save_daily_mode():
    with open(MODE_FILE, "w", encoding="utf-8") as file:
        file.write("daily")


def get_video_limit():
    return DEEP_LIMIT_PER_CHANNEL if is_deep_mode() else DAILY_LIMIT_PER_CHANNEL


def youtube_get(url, params):
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()

    if "error" in data:
        raise Exception(f"YouTube API error: {data['error']}")

    return data


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    while True:
        response = requests.post(
            url,
            json={
                "chat_id": CHAT_ID,
                "text": text,
                "disable_web_page_preview": False
            },
            timeout=30
        )

        if response.status_code == 429:
            retry_after = response.json().get("parameters", {}).get("retry_after", 10)
            time.sleep(retry_after + 1)
            continue

        response.raise_for_status()
        time.sleep(TELEGRAM_DELAY_SECONDS)
        break


def get_recent_video_ids(channel_id):
    limit = get_video_limit()
    video_ids = []
    page_token = None

    while len(video_ids) < limit:
        params = {
            "key": YOUTUBE_API_KEY,
            "channelId": channel_id,
            "part": "snippet",
            "order": "date",
            "type": "video",
            "maxResults": 50
        }

        if page_token:
            params["pageToken"] = page_token

        data = youtube_get(
            "https://www.googleapis.com/youtube/v3/search",
            params
        )

        for item in data.get("items", []):
            video_id = item.get("id", {}).get("videoId")
            if video_id:
                video_ids.append(video_id)

        page_token = data.get("nextPageToken")

        if not page_token:
            break

    return video_ids[:limit]


def get_video_details(video_ids):
    videos = []

    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i + 50]

        params = {
            "key": YOUTUBE_API_KEY,
            "id": ",".join(chunk),
            "part": "snippet"
        }

        data = youtube_get(
            "https://www.googleapis.com/youtube/v3/videos",
            params
        )

        videos.extend(data.get("items", []))

    return videos


def description_has_keyword(description):
    description_lower = description.lower()

    for keyword in KEYWORDS:
        if keyword.lower() in description_lower:
            return True

    return False


def format_date_tbilisi(published_at):
    dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
    tbilisi_dt = dt.astimezone(ZoneInfo("Asia/Tbilisi"))
    return tbilisi_dt.strftime("%Y-%m-%d %H:%M")


def validate_secrets():
    if not YOUTUBE_API_KEY:
        raise Exception("Missing YOUTUBE_API_KEY")

    if not TELEGRAM_TOKEN:
        raise Exception("Missing TELEGRAM_TOKEN")

    if not CHAT_ID:
        raise Exception("Missing CHAT_ID")


def main():
    validate_secrets()

    deep_mode = is_deep_mode()
    video_limit = get_video_limit()

    seen = load_seen()
    new_seen = set(seen)

    found_count = 0
    sent_count = 0

    for channel_id in CHANNEL_IDS:
        video_ids = get_recent_video_ids(channel_id)
        videos = get_video_details(video_ids)

        for video in videos:
            video_id = video.get("id")

            if not video_id:
                continue

            if video_id in seen:
                continue

            snippet = video.get("snippet", {})
            description = snippet.get("description", "")

            if description_has_keyword(description):
                found_count += 1

                published_at = format_date_tbilisi(snippet.get("publishedAt", ""))
                channel_title = snippet.get("channelTitle", "Unknown channel")
                video_title = snippet.get("title", "Untitled video")
                video_url = f"https://www.youtube.com/watch?v={video_id}"

                message = (
                    "Найдено видео с BlancVPN\n\n"
                    f"Дата: {published_at} Тбилиси\n"
                    f"Канал: {channel_title}\n"
                    f"Видео: {video_title}\n"
                    f"Ссылка: {video_url}"
                )

                send_telegram(message)
                sent_count += 1

            new_seen.add(video_id)

    save_seen(new_seen)

    if deep_mode:
        save_daily_mode()

    print(f"Mode before run: {'deep' if deep_mode else 'daily'}")
    print(f"Videos checked per channel: {video_limit}")
    print(f"Found new matches: {found_count}")
    print(f"Sent to Telegram: {sent_count}")
    print("Mode for next run: daily")


if __name__ == "__main__":
    main()
