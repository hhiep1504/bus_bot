import requests
import time
from datetime import datetime
import schedule

# ── CONFIG ──────────────────────────────────────────────────────────────
TELEGRAM_TOKEN = "8769232578:AAHdsHVCiZ0vZbTKo538op54LhINd73YmZI"
CHAT_ID        = "8303106105"
ATCO_CODE      = "3290YYA00174"          # Your bus stop ATCO code
BUS_STOP_NAME  = "The Barbican S-bound"       # Bus stop name for notifications
BUS_NUMBERS    = ["U2"]        # Only watch these services (or [] for all)
CHECK_INTERVAL = 2                  # Check every 2 minutes

TRANSPORT_APP_ID  = "a5856328"
TRANSPORT_APP_KEY = "86b23613d64238bc895f4e0dba5e38b5"

# ── SCHOOL SCHEDULE ─────────────────────────────────────────────────────
# Format: (day_of_week, class_time, "HH:MM")
# day_of_week: 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
ALERT_BEFORE_MINUTES = 60  # Alert starting this many minutes before class (1 hour)
BUS_ARRIVAL_WINDOW = (5, 30)  # Alert if bus arrives between 5-30 minutes from now

SCHOOL_SCHEDULE = [
    (0, "11:00", "Monday 11AM Class"),      # Thứ 2: 11h sáng
    (1, "11:00", "Tuesday 11AM Class"),     # Thứ 3: 11h sáng
    (4, "09:00", "Friday 9AM Class"),       # Thứ 5: 9h sáng
    (4, "16:00", "Friday 4PM Class"),       # Thứ 5: 4h chiều
    (5, "11:00", "Saturday 11AM Class"),    # Thứ 6: 11h sáng
    (5, "17:00", "Saturday 5PM Class"),     # Thứ 6: 5h chiều
]

# When to enable bus alerts (before class)
ALERT_MINUTES = None  # Will be calculated based on schedule
# ────────────────────────────────────────────────────────────────────────

def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"})

def get_departures():
    url = (
        f"https://transportapi.com/v3/uk/bus/stop/{ATCO_CODE}/live.json"
        f"?app_id={TRANSPORT_APP_ID}&app_key={TRANSPORT_APP_KEY}"
        f"&nextbuses=yes&group=no"
    )
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    departures = []
    for dep in data.get("departures", {}).get("all", []):
        departures.append({
            "service": dep.get("line"),
            "destination": dep.get("direction"),
            # Use best_departure_estimate (real-time) or aimed_departure_time
            "departure_time": dep.get("best_departure_estimate") or dep.get("aimed_departure_time"),
            "live": dep.get("best_departure_estimate") is not None,
        })
    return departures

def minutes_until(time_str: str) -> int | None:
    """Convert 'HH:MM' departure time to minutes from now."""
    try:
        now = datetime.now()
        dep = datetime.strptime(time_str, "%H:%M").replace(
            year=now.year, month=now.month, day=now.day
        )
        diff = (dep - now).total_seconds() / 60
        return int(diff) if diff >= 0 else None
    except Exception:
        return None

# Track which departures we've already alerted on (avoid duplicate messages)
alerted = set()

def get_next_class():
    """Get the next upcoming class."""
    now = datetime.now()
    current_day = now.weekday()
    current_time = now.strftime("%H:%M")
    
    # Check today's classes first
    for day, class_time, class_name in SCHOOL_SCHEDULE:
        if day == current_day and class_time > current_time:
            class_dt = datetime.strptime(class_time, "%H:%M")
            alert_time_str = f"{(class_dt.hour - 1):{:02d}:{(class_dt.minute - 45 if class_dt.minute >= 45 else class_dt.minute - 45 + 60):{:02d}}"
            return (class_day, class_time, class_name)
    
    # Otherwise, find next class
    days_ahead = 0
    while days_ahead <= 7:
        check_day = (current_day + days_ahead) % 7
        for day, class_time, class_name in SCHOOL_SCHEDULE:
            if day == check_day:
                return (day, class_time, class_name)
        days_ahead += 1
    
    return None

def should_alert_for_class():
    """Check if we're in the alert window (1 hour before class)."""
    now = datetime.now()
    current_day = now.weekday()
    current_time_minutes = now.hour * 60 + now.minute
    
    for day, class_time, class_name in SCHOOL_SCHEDULE:
        if day == current_day:
            class_hours, class_mins = map(int, class_time.split(":"))
            class_time_minutes = class_hours * 60 + class_mins
            alert_start = class_time_minutes - ALERT_BEFORE_MINUTES
            alert_end = class_time_minutes
            
            if alert_start <= current_time_minutes <= alert_end:
                return class_time, class_name
    
    return None

def check_buses():
    global alerted
    try:
        departures = get_departures()
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M')}] Error: {e}")
        return

    class_info = should_alert_for_class()
    if not class_info:
        return
    
    class_time, class_name = class_info
    
    # Find the best bus to catch (earliest in the arrival window)
    best_bus = None
    best_mins = float('inf')
    
    for dep in departures:
        service     = dep.get("service", "?")
        destination = dep.get("destination", "?")
        time_str    = dep.get("departure_time")
        is_live     = dep.get("live", False)

        if BUS_NUMBERS and service not in BUS_NUMBERS:
            continue
        if not time_str:
            continue

        mins = minutes_until(time_str)
        if mins is None:
            continue
        
        # Check if bus arrives within the alert window
        if BUS_ARRIVAL_WINDOW[0] <= mins <= BUS_ARRIVAL_WINDOW[1]:
            if mins < best_mins:
                best_mins = mins
                best_bus = {
                    "service": service,
                    "destination": destination,
                    "time_str": time_str,
                    "mins": mins,
                    "is_live": is_live,
                }
    
    # Send alert for the best bus found
    if best_bus:
        alert_key = f"{best_bus['service']}-{best_bus['time_str']}-{class_name}"
        if alert_key not in alerted:
            alerted.add(alert_key)
            live_tag = " <i>(live)</i>" if best_bus['is_live'] else ""
            msg = (
                f"🚌 <b>Bus {best_bus['service']}</b> → {best_bus['destination']}\n"
                f"📍 <b>{BUS_STOP_NAME}</b>\n"
                f"⏱ Arriving in <b>{best_bus['mins']} min</b> ({best_bus['time_str']}){live_tag}\n"
                f"🕐 For: <b>{class_name}</b>"
            )
            send_telegram(msg)
            print(f"Alert sent: Bus {best_bus['service']} in {best_bus['mins']} min for {class_name}")

def main():
    print(f"🚌 Bus bot started. Watching stop {ATCO_CODE} every {CHECK_INTERVAL} min.")
    send_telegram(f"🚌 Bus bot started! Watching stop <code>{ATCO_CODE}</code>")

    schedule.every(CHECK_INTERVAL).minutes.do(check_buses)
    check_buses()  # Run once immediately

    while True:
        schedule.run_pending()
        time.sleep(30)

if __name__ == "__main__":
    main()