import requests
import os
import json

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
NEWSROOM_URL = "https://news.sktelecom.com/feed"
LAST_ID_FILE = "last_id.json"

def get_latest_posts():
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(NEWSROOM_URL, headers=headers, timeout=10)
    import xml.etree.ElementTree as ET
    root = ET.fromstring(res.content)
    channel = root.find("channel")
    posts = []
    for item in channel.findall("item")[:10]:
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "")
        post_id = link.rstrip("/").split("/")[-1]
        categories = [c.text for c in item.findall("category") if c.text]
        is_press = "보도자료" in categories
        is_notice = "알려드립니다" in categories
        posts.append({"title": title, "link": link, "id": post_id, "is_press": is_press, "is_notice": is_notice})
    return posts

def send_telegram(title, link, is_press, is_notice):
    if is_press:
        label = "[보도자료] "
    elif is_notice:
        label = "[알려드립니다] "
    else:
        label = ""
    msg = f"📢 *SKT 뉴스룸 새 글*\n\n*{label}{title}*\n\n🔗 {link}"
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"},
        timeout=10
    )

def load_state():
    try:
        with open(LAST_ID_FILE) as f:
            return json.load(f)
    except:
        return {"last_id": "0", "sent_titles": []}

def save_state(last_id, sent_titles):
    with open(LAST_ID_FILE, "w") as f:
        json.dump({"last_id": last_id, "sent_titles": sent_titles[-50:]}, f, ensure_ascii=False)

def main():
    posts = get_latest_posts()
    if not posts:
        return

    state = load_state()
    last_id = state.get("last_id", "0")
    sent_titles = state.get("sent_titles", [])

    new_posts = [p for p in posts if int(p["id"]) > int(last_id)]

    sent_count = 0
    for post in reversed(new_posts):
