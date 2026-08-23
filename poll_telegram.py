"""
Telegram'dan gelen mesajları kontrol eder.
Sahibinden (OWNER) gelen ve hisse kodu gibi görünen her mesajı watchlist'e
ekler, analiz yapar ve sonucu geri gönderir.
"""

import os
import json
from analysis import analyze_ticker, send_telegram
import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
OWNER_CHAT_ID = str(os.environ.get("TELEGRAM_CHAT_ID", ""))

WATCHLIST_FILE = "watchlist.json"
OFFSET_FILE = "last_update_id.txt"


def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_watchlist(data):
    with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_offset():
    if os.path.exists(OFFSET_FILE):
        with open(OFFSET_FILE) as f:
            content = f.read().strip()
            return int(content) if content else 0
    return 0


def save_offset(offset):
    with open(OFFSET_FILE, "w") as f:
        f.write(str(offset))


def get_updates(offset):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    r = requests.get(url, params={"offset": offset, "timeout": 0}, timeout=20)
    r.raise_for_status()
    return r.json().get("result", [])


def normalize_ticker(text: str):
    t = text.strip().upper().replace(" ", "")
    if not t or len(t) > 15:
        return None
    if not all(c.isalnum() or c == "." for c in t):
        return None
    if not t.endswith(".IS"):
        t = t + ".IS"
    return t


def main():
    offset = load_offset()
    watchlist = load_watchlist()
    updates = get_updates(offset + 1)

    if not updates:
        print("Yeni mesaj yok.")
        return

    max_update_id = offset
    changed = False

    for upd in updates:
        max_update_id = max(max_update_id, upd["update_id"])
        msg = upd.get("message")
        if not msg or "text" not in msg:
            continue

        chat_id = str(msg["chat"]["id"])
        text = msg["text"]

        if chat_id != OWNER_CHAT_ID:
            continue

        if text.startswith("/"):
            continue

        ticker = normalize_ticker(text)
        if not ticker:
            send_telegram(chat_id, f"🤔 \"{text}\" bir hisse kodu gibi görünmüyor. Örnek: EREGL")
            continue

        if ticker not in watchlist:
            watchlist.append(ticker)
            changed = True
            prefix = f"✅ <b>{ticker}</b> takip listene eklendi.\n\n"
        else:
            prefix = f"ℹ️ {ticker} zaten listende, güncel analiz:\n\n"

        result = analyze_ticker(ticker)
        send_telegram(chat_id, prefix + result)

    if changed:
        save_watchlist(watchlist)
    save_offset(max_update_id)


if __name__ == "__main__":
    main()
