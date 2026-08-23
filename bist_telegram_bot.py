"""Her sabah 7'de çalışan günlük rapor scripti. watchlist.json içindeki hisseleri analiz eder."""

import os
import json
from datetime import datetime
from analysis import analyze_ticker, send_telegram

CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
WATCHLIST_FILE = "watchlist.json"

VARSAYILAN_LISTE = ["THYAO.IS", "ASELS.IS", "GARAN.IS", "SISE.IS", "KCHOL.IS"]


def load_watchlist():
    if os.path.exists(WATCHLIST_FILE):
        with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if data:
                return data
    return VARSAYILAN_LISTE


def main():
    tickers = load_watchlist()
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    message_parts = [f"📊 <b>Günlük BIST Piyasa Raporu</b>\n{now}\n"]

    for ticker in tickers:
        message_parts.append(analyze_ticker(ticker))

    full_message = "\n\n".join(message_parts)

    if len(full_message) > 4000:
        for i in range(0, len(full_message), 4000):
            send_telegram(CHAT_ID, full_message[i:i + 4000])
    else:
        send_telegram(CHAT_ID, full_message)

    print("Rapor gönderildi.")


if __name__ == "__main__":
    main()
