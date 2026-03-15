import os
import requests
from datetime import datetime, timezone, date, timedelta

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

BOOK_URL = "https://ovenbirdsg.com/?page_id=45"
API_URL = "https://www.restaurants.sg/apiv4/services.php/booking/rdate/"

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://www.restaurants.sg",
    "Referer": "https://www.restaurants.sg/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
}

def get_target_dates():
    target_months = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    target_weekdays = {4, 5}
    dates = []
    for month in target_months:
        start = date(2026, month, 1)
        end = date(2027, 1, 1) if month == 12 else date(2026, month + 1, 1)
        current = start
        while current < end:
            if current.weekday() in target_weekdays:
                if current > date.today():
                    dates.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)
    return dates

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})

def parse_slots(raw_slots):
    parsed = []
    for slot in raw_slots:
        parts = slot.split("|")
        if len(parts) >= 5:
            party_size = parts[2]
            time = parts[4]
            session = parts[7] if len(parts) > 7 else "dinner"
            parsed.append(f"{time} (party of {party_size}, {session})")
    return sorted(set(parsed))

def check_availability(target_date):
    payload = {
        "restaurant": "SG_SG_R_OvenbirdAndHappyLily",
        "rdate": target_date,
        "product": "Ovenbird",
        "bkparam": "",
        "appname": "be",
        "token": "abcdef"
    }
    response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=15)
    data = response.json()
    raw_slots = data.get("data", [])

    # Filter to only slots where first field is "1" (believed to = available)
    # NOTE: 70% confidence on this interpretation — to be verified against a live slot
    available = [s for s in raw_slots if s.split("|")[0] == "1"]
    return available

def main():
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERROR: Missing Telegram credentials.")
        exit(1)

    now = datetime.now(timezone.utc).strftime('%H:%M UTC')
    target_dates = get_target_dates()
    print(f"Ovenbird check at {now} — {len(target_dates)} dates")

    found_any = False

    for target_date in target_dates:
        try:
            print(f"  Checking {target_date}...")
            raw_slots = check_availability(target_date)

            if raw_slots:
                readable = parse_slots(raw_slots)
                send_telegram(
                    f"OVENBIRD - SLOTS OPEN!\n"
                    f"Date: {target_date}\n"
                    f"Times:\n" +
                    "\n".join(f"  • {s}" for s in readable) +
                    f"\n\nBook NOW: {BOOK_URL}"
                )
                print(f"  Alert sent for {target_date}: {readable}")
                found_any = True

        except Exception as e:
            print(f"  Error checking {target_date}: {e}")

    if not found_any:
        print("No slots found across any target dates.")

if __name__ == "__main__":
    main()
