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
    print("HTTP 상태코드:", res.status_code)

    import xml.etree.ElementTree as ET
    root = ET.fromstring(res.content)
    channel = root.find("channel")
    if channel is None:
        print("channel 태그를 찾을 수 없음")
        return []

    items = channel.findall("item")
    print("item 개수:", len(items))

    posts = []
    for item in items[:10]:
        title = item.findtext("title", "").strip()
        link = item.findtext("link", "")
        post_id = link.rstrip("/").split("/")[-1]
        categories = [c.text for c in item.findall("category") if c.text]
        is_press = "보도자료" in categories
        is_notice = "알려드립니다" in categories
        posts.append({
            "title": title,
            "link": link,
            "id": post_id,
            "is_press": is_press,
            "is_notice": is_notice,
        })
    return posts


def send_telegram(title, link, is_press, is_notice):
    if is_press:
        label = "[보도자료] "
    elif is_notice:
        label = "[알려드립니다] "
    else:
        label = ""
    msg = "📢 SKT 뉴스룸 새 글\n\n" + label + title + "\n\n🔗 " + link
    res = requests.post(
        "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage",
        json={"chat_id": CHAT_ID, "text": msg},
        timeout=10,
    )
    if res.status_code == 200:
        print("발송 성공: " + title)
        return True
    else:
        print("발송 실패 (" + str(res.status_code) + "): " + res.text)
        return False


def load_state():
    try:
        with open(LAST_ID_FILE) as f:
            return json.load(f)
    except Exception:
        return {"last_id": "0", "sent_titles": []}


def save_state(last_id, sent_titles):
    with open(LAST_ID_FILE, "w") as f:
        json.dump({"last_id": last_id, "sent_titles": sent_titles[-50:]}, f, ensure_ascii=False)


def main():
    posts = get_latest_posts()
    if not posts:
        print("posts가 비어 있어 종료")
        return

    state = load_state()
    last_id = state.get("last_id", "0")
    sent_titles = state.get("sent_titles", [])

    new_posts = []
    for p in posts:
        if int(p["id"]) > int(last_id):
            new_posts.append(p)

    if not new_posts:
        print("신규 게시물 없음")
        return

    sent_count = 0
    new_last_id = last_id

    for post in reversed(new_posts):
        if post["title"] in sent_titles:
            print("중복 제목 건너뜀: " + post["title"])
            new_last_id = post["id"]
            continue

        success = send_telegram(post["title"], post["link"], post["is_press"], post["is_notice"])

        if success:
            sent_titles.append(post["title"])
            new_last_id = post["id"]
            sent_count += 1
            if post["is_press"]:
                tag = "보도자료"
            elif post["is_notice"]:
                tag = "알려드립니다"
            else:
                tag = "일반"
            print("(" + tag + "): " + post["title"])
        else:
            print("발송 실패로 last_id 업데이트 중단: " + post["title"])
            break

    save_state(new_last_id, sent_titles)
    print("완료: 신규 " + str(len(new_posts)) + "개 중 " + str(sent_count) + "개 발송")


if __name__ == "__main__":
    main()
