"""Ortak fonksiyonlar: analiz ve Telegram gönderimi."""

import os
import yfinance as yf
import pandas as pd
import requests

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")


def send_telegram(chat_id: str, text: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
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
            return f"⚠️ <b>{ticker}</b>: fiyat verisi alınamadı (kod yanlış olabilir)"

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
