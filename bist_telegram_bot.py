"""
BIST Günlük Piyasa Analiz Botu
- F/K (P/E), PD/DD gibi temel analiz oranlarını hesaplar
- SMA (hareketli ortalama) ve RSI ile teknik analiz yapar
- Sonucu Telegram'a mesaj olarak gönderir
"""

import os
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

# ---------------- AYARLAR ----------------
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "BURAYA_BOT_TOKENINIZI_YAZIN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "BURAYA_CHAT_ID_YAZIN")

# İzlemek istediğiniz hisseler (BIST hisseleri ".IS" ile biter)
TICKERS = ["THYAO.IS", "ASELS.IS", "GARAN.IS", "SISE.IS", "KCHOL.IS"]
# ---------------------------------------------------------------


def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=payload, timeout=15)
        if r.status_code != 200:
            print("Telegram gönderim hatası:", r.text)
    except Exception as e:
        print("Telegram bağlantı hatası:", e)


def calc_rsi(series: pd.Series, period: int = 14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1] if not rsi.empty else None


def analyze_ticker(ticker: str) -> str:
    try:
        t = yf.Ticker(ticker)
        info = t.info
        hist = t.history(period="3mo")

        if hist.empty:
            return f"⚠️ <b>{ticker}</b>: fiyat verisi alınamadı"

        price = hist["Close"].iloc[-1]
        sma20 = hist["Close"].rolling(20).mean().iloc[-1]
        rsi = calc_rsi(hist["Close"])

        pe = info.get("trailingPE")
        fwd_pe = info.get("forwardPE")
        pb = info.get("priceToBook")

        trend = "🔼 Yükseliş eğiliminde" if price > sma20 else "🔽 Düşüş eğiliminde"
        if rsi is None:
            rsi_yorum = "hesaplanamadı"
        elif rsi > 70:
            rsi_yorum = "aşırı alım bölgesi"
        elif rsi < 30:
            rsi_yorum = "aşırı satım bölgesi"
        else:
            rsi_yorum = "nötr bölge"

        lines = [
            f"<b>{ticker}</b>",
            f"Fiyat: {price:.2f} TL",
            f"F/K: {pe:.2f}" if pe else "F/K: veri yok",
            f"Tahmini F/K: {fwd_pe:.2f}" if fwd_pe else None,
            f"PD/DD: {pb:.2f}" if pb else None,
            f"SMA20: {sma20:.2f} TL — {trend}",
            f"RSI(14): {rsi:.1f} ({rsi_yorum})" if rsi is not None else None,
        ]
        return "\n".join(l for l in lines if l)

    except Exception as e:
        return f"⚠️ <b>{ticker}</b> analiz edilirken hata oluştu: {e}"


def main():
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    message_parts = [f"📊 <b>Günlük BIST Piyasa Raporu</b>\n{now}\n"]

    for ticker in TICKERS:
        message_parts.append(analyze_ticker(ticker))

    full_message = "\n\n".join(message_parts)

    if len(full_message) > 4000:
        for i in range(0, len(full_message), 4000):
            send_telegram(full_message[i:i + 4000])
    else:
        send_telegram(full_message)

    print("Rapor gönderildi.")


if __name__ == "__main__":
    main()
