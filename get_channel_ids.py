import os
import requests

API_KEY = os.getenv("YOUTUBE_API_KEY")

handles = [
    "Kolezev",
    "Web3nity",
    "RuslanBelyy",
    "VadimKey",
    "skazhigordeevoy",
    "Zhukova_PS",
    "Spoontamer",
    "MackNack",
    "varlamov",
    "Ekaterina_Schulmann",
    "radiodolin",
    "vraevskiy",
    "AlexShevstsov",
    "Max_Katz",
    "vdud"
]

def get_channel_id(handle):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": API_KEY,
        "q": handle,
        "type": "channel",
        "part": "snippet",
        "maxResults": 1
    }
    r = requests.get(url, params=params).json()
    items = r.get("items", [])
    if not items:
        return None
    return items[0]["snippet"]["channelId"]

def main():
    for h in handles:
        cid = get_channel_id(h)
        print(h, "→", cid)

if __name__ == "__main__":
    main()
