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
    target_months = [3, 4, 5, 6, 7, 8, 9, 10, 11, 12]  # Mar to Dec
    target_weekdays = {4, 5}  # 4 = Friday, 5 = Saturday
    dates = []
    for month in target_months:
        # Get all days in the month
        start = date(2026, month, 1)
        # Find last day of month
        if month == 12:
            end = date(2027, 1, 1)
        else:
            end = date(2026, month + 1, 1)
        current = start
        while current < end:
            if current.weekday() in target_weekdays:
                # Only include future dates
                if current > date.today():
                    dates.append(current.strftime("%Y-%m-%d"))
            current += timedelta(days=1)
    return dates

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})

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
    return data.get("data", [])

def main():
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("ERROR: Missing Telegram credentials.")
        exit(1)

    now = datetime.now(timezone.utc).strftime('%H:%M UTC')
    target_dates = get_target_dates()
    print(f"Ovenbird check running at {now}")
    print(f"Checking {len(target_dates)} dates (Fri & Sat, Mar-Dec 2026)")

    found_any = False

    for target_date in target_dates:
        try:
            print(f"  Checking {target_date}...")
            slots = check_availability(target_date)
            if slots:
                send_telegram(
                    f"OVENBIRD - SLOTS OPEN!\n"
                    f"Date: {target_date}\n"
                    f"Available: {slots}\n"
                    f"Book NOW: {BOOK_URL}"
                )
                print(f"  Alert sent for {target_date}! Slots: {slots}")
                found_any = True
        except Exception as e:
            print(f"  Error checking {target_date}: {e}")

    if not found_any:
        print("No slots found across any target dates.")

if __name__ == "__main__":
    main()
