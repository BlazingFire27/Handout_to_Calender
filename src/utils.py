import re
from datetime import datetime, timedelta 

def predefined(date_from_llm, time_str, event_name):
    date_clean = date_from_llm.strip()
    date_iso = date_clean

    formats = [
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d/%m/%y",
        "%d-%m-%y",
        "%d.%m.%Y",
        "%Y-%m-%d",
        "%d-%b-%Y"
    ]

    for fmt in formats:
        try:
            date_obj = datetime.strptime(date_clean, fmt)
            date_iso = date_obj.strftime("%Y-%m-%d")
            break
        except ValueError:
            continue

    event_lower = normalize_event_name(event_name).lower()
    time_clean = time_str.strip().upper()

    is_compre = (
        "comprehensive" in event_lower or
        "compre" in event_lower or
        "final exam" in event_lower
    )

    if is_compre:
        if "FN" in time_clean:
            return f"{date_iso}T10:00:00", f"{date_iso}T13:00:00"
        elif "AN" in time_clean:
            return f"{date_iso}T14:00:00", f"{date_iso}T17:00:00"

    match = re.search(r"(\d+)(?::(\d+))?", time_clean)
    
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        is_pm = "PM" in time_clean
        
        if 8 <= hour <= 11:
            start_hour = hour
        elif hour == 12:
            start_hour = 12 if is_pm else 12
            if "AM" in time_clean: start_hour = 0
        else:
            start_hour = hour + 12 if is_pm else hour
        try:
            start_dt_str = f"{date_iso} {start_hour:02d}:{minute:02d}:00"
            start_dt = datetime.strptime(start_dt_str, "%Y-%m-%d %H:%M:%S")
            
            end_dt = start_dt + timedelta(hours=1, minutes=30)
            
            return start_dt.isoformat(), end_dt.isoformat()
        
        except ValueError:
            pass

        # start_iso = f"{start_hour:02d}:00:00"
        # end_hour = start_hour + 1
        
        # return f"{date_iso}T{start_iso}", f"{date_iso}T{end_hour:02d}:30:00"

    return "Time not found", date_iso

def clean_subject_key(sub_name):
    if not sub_name: return ""
    return sub_name.lower().split('(')[0].strip()

def normalize_event_name(event_name):
    name = event_name.lower().strip()

    if any(x in name for x in ['compre', 'final exam', 'end sem', 'finals']):
        return "Comprehensive Exam"
    if any(x in name for x in ["midsem", "mid-sem", "mid sem"]):
        return "MidSem Exam"

    return event_name.title()