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
    for item in channel.findall("item")[:5]:
        title = item.findtext("title", "")
        link = item.findtext("link", "")
        post_id = link.rstrip("/").split("/")[-1]
        posts.append({"title": title, "link": link, "id": post_id})
    return posts

def send_telegram(title, link):
    msg = f"📢 *SKT 뉴스룸 새 글*\n\n*{title}*\n\n🔗 {link}"
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"},
        timeout=10
    )

def load_last_id():
    try:
        with open(LAST_ID_FILE) as f:
            return json.load(f).get("last_id", "0")
    except:
        return "0"

def save_last_id(post_id):
    with open(LAST_ID_FILE, "w") as f:
        json.dump({"last_id": post_id}, f)

def main():
    posts = get_latest_posts()
    if not posts:
        return

    last_id = load_last_id()
    new_posts = [p for p in posts if int(p["id"]) > int(last_id)]

    # 오래된 순서대로 발송
    for post in reversed(new_posts):
        send_telegram(post["title"], post["link"])
        print(f"발송: {post['title']}")

    if new_posts:
        save_last_id(posts[0]["id"])

if __name__ == "__main__":
    main()
