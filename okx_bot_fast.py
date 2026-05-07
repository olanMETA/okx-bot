import requests
import json
import time
import os
from datetime import datetime

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = "7948417131:AAFAcDwmYvpVQ4MvexcqvMI-CZtaXZigJHA"
CHAT_ID = "1780854025"
CHECK_INTERVAL = 30  # проверка каждые 30 секунд
SEEN_FILE = "seen_instruments.json"
# ================================

# OKX публичные API endpoints
SPOT_URL    = "https://www.okx.com/api/v5/public/instruments?instType=SPOT"
FUTURES_URL = "https://www.okx.com/api/v5/public/instruments?instType=SWAP"  # бессрочные фьючерсы

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id": CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def get_instruments(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        data = r.json()
        if data.get("code") == "0":
            return data.get("data", [])
    except Exception as e:
        print(f"API error: {e}")
    return []

def format_message(inst, inst_type):
    symbol = inst.get("instId", "")
    base = inst.get("baseCcy", "")
    quote = inst.get("quoteCcy", "")
    
    if inst_type == "SPOT":
        emoji = "💱"
        type_text = "Спотовая торговля"
        link = f"https://www.okx.com/trade-spot/{symbol.lower()}"
    else:
        emoji = "📊"
        type_text = "Бессрочный фьючерс (SWAP)"
        link = f"https://www.okx.com/trade-swap/{symbol.lower()}"

    now = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    
    msg = (
        f"{emoji} <b>НОВЫЙ ЛИСТИНГ OKX!</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🪙 <b>Токен:</b> {base}\n"
        f"📌 <b>Пара:</b> {symbol}\n"
        f"📂 <b>Тип:</b> {type_text}\n"
        f"🕐 <b>Время:</b> {now}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔗 <a href='{link}'>Открыть на OKX</a>"
    )
    return msg

def main():
    print("=" * 50)
    print("OKX Fast Listings Bot запущен!")
    print(f"Проверка каждые {CHECK_INTERVAL} секунд через API")
    print("=" * 50)

    send_telegram(
        "✅ <b>OKX Fast Bot запущен!</b>\n\n"
        "🔄 Проверка каждые <b>30 секунд</b>\n"
        "📡 Источник: официальный API OKX\n"
        "🔔 Слежу за SPOT и SWAP листингами"
    )

    seen = load_seen()

    # Первый запуск — сохраняем всё что есть
    if not seen:
        print("Первый запуск — загружаю текущие инструменты...")
        spot = get_instruments(SPOT_URL)
        swaps = get_instruments(FUTURES_URL)
        all_ids = [i["instId"] for i in spot + swaps]
        seen = set(all_ids)
        save_seen(seen)
        print(f"Сохранено {len(seen)} инструментов (спот + своп)")
        send_telegram(f"📋 Загружено <b>{len(spot)}</b> спотовых и <b>{len(swaps)}</b> своп пар.\nСлежу за новыми...")

    while True:
        try:
            spot_list  = get_instruments(SPOT_URL)
            swap_list  = get_instruments(FUTURES_URL)

            new_found = []

            for inst in spot_list:
                if inst["instId"] not in seen:
                    new_found.append((inst, "SPOT"))
                    seen.add(inst["instId"])

            for inst in swap_list:
                if inst["instId"] not in seen:
                    new_found.append((inst, "SWAP"))
                    seen.add(inst["instId"])

            if new_found:
                save_seen(seen)
                for inst, itype in new_found:
                    msg = format_message(inst, itype)
                    send_telegram(msg)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Новый листинг: {inst['instId']} ({itype})")
                    time.sleep(0.5)
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Новых листингов нет")

        except Exception as e:
            print(f"Ошибка: {e}")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
