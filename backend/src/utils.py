import re
from datetime import datetime, timedelta
import dateparser
from dateparser.search import search_dates
from ics import Calendar, Event
import arrow
import requests
import urllib.parse
import concurrent.futures
import os
from dotenv import load_dotenv

load_dotenv()

def predefined(date_raw, time_str, event_name, user_format="DMY"):
    date_clean = date_raw.strip()
    date_iso = date_clean

    # Use deterministic dateparser with user preference to eliminate bias
    base_date = datetime(2025, 1, 1)
    
    # Use search_dates to extract dates buried in text (e.g. "Tentative- 15th Nov")
    found_dates = search_dates(
        date_clean,
        settings={'DATE_ORDER': user_format, 'RELATIVE_BASE': base_date}
    )
    
    if found_dates:
        # search_dates returns a list of tuples: [("substring", datetime_obj)]
        date_obj = found_dates[0][1]
        date_iso = date_obj.strftime("%Y-%m-%d")
    else:
        # Fallback to direct parse
        date_obj = dateparser.parse(
            date_clean, 
            settings={'DATE_ORDER': user_format, 'RELATIVE_BASE': base_date}
        )
        if date_obj:
            date_iso = date_obj.strftime("%Y-%m-%d")
    
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

    times = list(re.finditer(r"(\d{1,2})(?::(\d{2}))?", time_clean))

    if ("MIN" in time_clean or "HRS" in time_clean) and not (":" in time_clean or "AM" in time_clean or "PM" in time_clean):
        return "Time not found", date_iso
      
    if not times:
        return "Time not found", date_iso
    
    start_dt = None
    end_dt = None

    is_pm = "PM" in time_clean
    is_am = "AM" in time_clean

    t1 = times[0]
    hour1 = int(t1.group(1))
    minute1 = int(t1.group(2) or 0)

    try:        
        if len(times) > 1:
            t2 = times[1]
            hour2 = int(t2.group(1))
            minute2 = int(t2.group(2) or 0)

            only_pm = is_pm and not is_am

            if not is_pm and not is_am and hour2 < hour1:
                only_pm = True

            hour2_24 = to_24h(hour2, only_pm)
            end_candid = datetime.strptime(f"{date_iso} {hour2_24:02d}:{minute2:02d}:00", "%Y-%m-%d %H:%M:%S")

            hour1_am = to_24h(hour1, False)
            candid_am = datetime.strptime(f"{date_iso} {hour1_am:02d}:{minute1:02d}:00", "%Y-%m-%d %H:%M:%S")

            h1_pm = to_24h(hour1, True)
            candid_pm = datetime.strptime(f"{date_iso} {h1_pm:02d}:{minute1:02d}:00", "%Y-%m-%d %H:%M:%S")

            difference_am = (end_candid - candid_am).total_seconds() / 3600
            difference_pm = (end_candid - candid_pm).total_seconds() / 3600

            if 0.5 <= difference_pm <= 6:
                start_dt = candid_pm
            elif 0.5 <= difference_am <= 6:
                start_dt = candid_am
            else:
                start_dt = candid_am

            if end_candid < start_dt:
                end_candid += timedelta(hours=12)
            
            end_dt = end_candid

        else:
            is_pm_start = is_pm

            if not is_pm and not is_am:
                if 1 <= hour1 <= 6:
                    is_pm_start = True
            
            hour1_final = to_24h(hour1, is_pm_start)

            start_dt = datetime.strptime(f"{date_iso} {hour1_final:02d}:{minute1:02d}:00", "%Y-%m-%d %H:%M:%S")
            end_dt = start_dt + timedelta(hours=1, minutes=30)

        return start_dt.isoformat(), end_dt.isoformat()
    
    except ValueError:
        pass
        
    return "Time not found", date_iso

def clean_subject_key(sub_name):
    if not sub_name: return ""
    return sub_name.lower().split('(')[0].strip()

def normalize_event_name(event_name):
    # Simply return the title-cased name to prevent over-aggressive normalization 
    # and generalize perfectly to all Indian colleges based on raw AI extraction.
    return event_name.strip().title()

# THANK YOU GEMINI FOR TO_24H FUNCTION CODE AND IDEA TO USE THIS
def to_24h(h, is_pm):
        if is_pm:
            if h < 12: return h + 12
            if h == 12: return 12
            return h
        else:
            if h == 12: return 0 # 12 AM
            return h

def save_ics(events, filename):
    c = Calendar()

    for item in events:
        e = Event()
        e.name = item['Subject']

        try:
            if "TIME TBA" in item['Subject']:
                date_only = item['Start_DateTime'].split("T")[0]
                e.begin = arrow.get(date_only)
                e.make_all_day()
            else:
                e.begin = arrow.get(item['Start_DateTime']).replace(tzinfo='Asia/Kolkata')
                e.end = arrow.get(item['End_DateTime']).replace(tzinfo='Asia/Kolkata')

            description = (
                f"Event Name: {item['Event_Name']}\n"
                f"Format: {item['Format']}\n"
                f"Weightage: {item['Weightage']}\n"
                f"Raw Time String: {item['Raw_Time_String']}\n"
                f"++++++++++++++++++++++++++\n"
                f"Generated by AI Agent"
            )

            e.description = description
            c.events.add(e)
            
        except Exception as err:
            print(f"  ⚠️ Skipping ICS event '{item['Subject']}': Invalid or missing date ({err})")
            continue

    with open(filename, 'w', encoding="utf-8") as f:
        f.writelines(c.serialize())
    
    print(f"ICS file saved as {filename}")

def fetch_book_metadata(title, author=""):
    """Fetches book metadata from Google Books API with a fallback to title-only search."""
    if not title:
        return {"thumbnail_url": "", "info_link": ""}
        
    def _search(query):
        api_key = os.getenv("GOOGLE_BOOK_API_KEY")
        url = f"https://www.googleapis.com/books/v1/volumes?q={urllib.parse.quote(query)}&maxResults=1"
        if api_key:
            url += f"&key={api_key}"
            
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                data = response.json()
                if "items" in data and len(data["items"]) > 0:
                    volume_info = data["items"][0].get("volumeInfo", {})
                    thumbnail = volume_info.get("imageLinks", {}).get("thumbnail", "")
                    info_link = volume_info.get("infoLink", "")
                    # Upgrade thumbnail to https if possible
                    if thumbnail.startswith("http:"):
                        thumbnail = thumbnail.replace("http:", "https:")
                    return {"thumbnail_url": thumbnail, "info_link": info_link}
        except Exception:
            pass
        return None

    # Step 1: Search with Title + Author
    query = f"intitle:{title}"
    if author and str(author).strip().lower() not in ["n/a", "unknown"]:
        query += f"+inauthor:{author}"
        
    result = _search(query)
    
    # Step 2: Fallback to Title only
    if not result and author:
        fallback_query = f"intitle:{title}"
        result = _search(fallback_query)
        
    if result:
        return result
        
    return {"thumbnail_url": "", "info_link": ""}

def enrich_refs_parallel(refs):
    """Takes a list of reference dicts and enriches them with Google Books data in parallel."""
    if not refs:
        return

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_ref = {
            executor.submit(fetch_book_metadata, ref.get("title", ""), ref.get("author", "")): ref 
            for ref in refs
        }
        
        for future in concurrent.futures.as_completed(future_to_ref):
            ref = future_to_ref[future]
            try:
                metadata = future.result()
                if metadata:
                    ref["thumbnail_url"] = metadata.get("thumbnail_url", "")
                    ref["info_link"] = metadata.get("info_link", "")
                else:
                    ref["thumbnail_url"] = ""
                    ref["info_link"] = ""
            except Exception:
                ref["thumbnail_url"] = ""
                ref["info_link"] = ""
