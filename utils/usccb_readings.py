import os
import requests
from bs4 import BeautifulSoup
import json
import csv
import re
import time
from datetime import date, timedelta
from dateutil.easter import easter # Required for liturgical date calculations
from dateutil.relativedelta import relativedelta, SU, TH # For finding Sundays, etc.

# --- CONFIGURATION ---
# Use the full date range for production runs
START_DATE = date(2025, 10, 23)
END_DATE = date(2026, 12, 31)
# DEBUG_DATES = [date(2025, 10, 23), date(2025, 10, 26)] # Keep commented out for full runs
OUTPUT_DIR = "../data_usccb" # Relative path from utils/ directory
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "usccb-readings.csv") # Use production filenames
OUTPUT_JSON = os.path.join(OUTPUT_DIR, "usccb-readings.json") # Use production filenames
BASE_URL = "https://bible.usccb.org/bible/readings/"
REQUEST_DELAY_SECONDS = 1 # Be polite to the server

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Mapping for book slugs (lowercase, hyphenated)
BOOK_SLUG_MAP = {
    "genesis": "genesis", "exodus": "exodus", "leviticus": "leviticus", "numbers": "numbers", "deuteronomy": "deuteronomy",
    "joshua": "joshua", "judges": "judges", "ruth": "ruth", "1 samuel": "1-samuel", "2 samuel": "2-samuel",
    "1 kings": "1-kings", "2 kings": "2-kings", "1 chronicles": "1-chronicles", "2 chronicles": "2-chronicles",
    "ezra": "ezra", "nehemiah": "nehemiah", "tobit": "tobit", "judith": "judith", "esther": "esther",
    "1 maccabees": "1-maccabees", "2 maccabees": "2-maccabees", "job": "job", "psalms": "psalms", "proverbs": "proverbs",
    "ecclesiastes": "ecclesiastes", "song of songs": "song-of-songs", "wisdom": "wisdom", "sirach": "sirach",
    "isaiah": "isaiah", "jeremiah": "jeremiah", "lamentations": "lamentations", "baruch": "baruch", "ezekiel": "ezekiel",
    "daniel": "daniel", "hosea": "hosea", "joel": "joel", "amos": "amos", "obadiah": "obadiah",
    "jonah": "jonah", "micah": "micah", "nahum": "nahum", "habakkuk": "habakkuk", "zephaniah": "zephaniah",
    "haggai": "haggai", "zechariah": "zechariah", "malachi": "malachi", "matthew": "matthew", "mark": "mark",
    "luke": "luke", "john": "john", "acts": "acts", "romans": "romans", "1 corinthians": "1-corinthians",
    "2 corinthians": "2-corinthians", "galatians": "galatians", "ephesians": "ephesians", "philippians": "philippians",
    "colossians": "colossians", "1 thessalonians": "1-thessalonians", "2 thessalonians": "2-thessalonians",
    "1 timothy": "1-timothy", "2 timothy": "2-timothy", "titus": "titus", "philemon": "philemon",
    "hebrews": "hebrews", "james": "james", "1 peter": "1-peter", "2 peter": "2-peter",
    "1 john": "1-john", "2 john": "2-john", "3 john": "3-john", "jude": "jude", "revelation": "revelation",
    # Add common abbreviations found on USCCB site
    "ps": "psalms", "1 cor": "1-corinthians", "2 cor": "2-corinthians", "gal": "galatians", "eph": "ephesians",
    "phil": "philippians", "col": "colossians", "1 thes": "1-thessalonians", "2 thes": "2-thessalonians",
    "1 tm": "1-timothy", "2 tm": "2-timothy", "ti": "titus", "phlm": "philemon", "heb": "hebrews",
    "jas": "james", "1 pt": "1-peter", "2 pt": "2-peter", "1 jn": "1-john", "2 jn": "2-john", "3 jn": "3-john",
    "jud": "jude", "rv": "revelation",
}

# --- Liturgical Color Definitions ---
WHITE = "White"
RED = "Red"
GREEN = "Green"
VIOLET = "Violet"
ROSE = "Rose"
BLACK = "Black"

# --- HELPER FUNCTIONS ---

def get_soup(url):
    """Fetches a URL and returns a BeautifulSoup object."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=20) # Added timeout
        response.raise_for_status() # Raises an exception for bad status codes (4xx or 5xx)
        return BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.HTTPError as e:
        # Specifically catch HTTP errors (like 404) to allow fallback
        print(f"  -> HTTP Error fetching {url}: {e.response.status_code}")
        return None # Indicate failure but allow fallback
    except requests.exceptions.RequestException as e:
        print(f"  -> Network Error fetching {url}: {e}")
        return None # Indicate failure but allow fallback

def daterange(start_date, end_date):
    """Generator for dates in a range."""
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)

def parse_reference_to_link(ref_string):
    """
    Parses a scripture reference and generates a local link pointing to the
    verse *before* the reading starts, or the chapter page if it starts at verse 1.
    Removes the 'v' prefix from the fragment.
    """
    if not ref_string or ref_string.lower() == 'none':
        return None

    ref_string = ref_string.replace('NABRE', '').strip()

    # Match book name (possibly starting with a digit) followed by chapter:verse
    match = re.match(r'^(\d?\s?[A-Za-z]+(?:\s[A-Za-z]+)?)\s*(\d+):([\da-z]+)', ref_string, re.IGNORECASE)
    if not match:
        # Special case for Psalms
        psalm_match = re.match(r'^(Psalm|Ps)\s*(\d+):([\da-z]+)', ref_string, re.IGNORECASE)
        if psalm_match:
            book_name_part = "Psalms"
            chapter_str = psalm_match.group(2)
            verse_part = psalm_match.group(3)
        else:
            # print(f"  -> DEBUG [parse_link]: Could not parse book/chap/verse from: '{ref_string}'")
            return None
    else:
        book_name_part = match.group(1).strip()
        chapter_str = match.group(2)
        verse_part = match.group(3)

    # Normalize book name and get slug
    book_name_lower = book_name_part.lower()
    book_slug = BOOK_SLUG_MAP.get(book_name_lower)
    if not book_slug:
        # Try finding partial match
        for map_key, map_slug in BOOK_SLUG_MAP.items():
             if map_key in book_name_lower or book_name_lower in map_key:
                  book_slug = map_slug
                  break # Use the first partial match found
        if not book_slug:
             # print(f"  -> DEBUG [parse_link]: Book name '{book_name_part}' not found in slug map.")
             return None

    try:
        chapter_padded = chapter_str.zfill(2)
        
        # Extract just the numeric part of the starting verse
        start_verse_num_match = re.match(r'^(\d+)', verse_part)
        if not start_verse_num_match:
             # print(f"  -> DEBUG [parse_link]: Could not extract verse number from '{verse_part}' in '{ref_string}'")
             return None
        start_verse_num = int(start_verse_num_match.group(1))

        # Determine the fragment identifier
        fragment = ""
        if start_verse_num > 1:
            preceding_verse_num = start_verse_num - 1
            fragment = f"#{preceding_verse_num}" # No 'v' prefix

        link = f"bible/{book_slug}-{chapter_padded}.html{fragment}"
        # print(f"  -> DEBUG [parse_link]: Generated link '{link}' from '{ref_string}' (starts verse {start_verse_num})")
        return link

    except ValueError:
        # print(f"  -> DEBUG [parse_link]: Could not parse chapter/verse numbers in: '{ref_string}'")
        return None

def get_liturgical_color(target_date, day_name):
    """Determines the liturgical color based on the date and name of the day."""
    if day_name is None: day_name = "" # Handle cases where name wasn't scraped
    year = target_date.year
    month = target_date.month
    day = target_date.day
    weekday = target_date.weekday() # Monday is 0 and Sunday is 6

    # --- Calculate Key Liturgical Dates ---
    easter_date = easter(year)
    ash_wednesday = easter_date - timedelta(days=46)
    palm_sunday = easter_date - timedelta(days=7)
    good_friday = easter_date - timedelta(days=2)
    pentecost = easter_date + timedelta(days=49)
    # Baptism of the Lord: Sunday after Epiphany (Jan 6)
    epiphany = date(year, 1, 6)
    baptism_of_lord = epiphany + relativedelta(weekday=SU(+1))
    # Start of Advent: 4th Sunday before Christmas. Find Sunday before Nov 27th.
    first_sunday_advent = date(year, 11, 27) + relativedelta(weekday=SU(-1))

    # --- Color Logic (Priority Order) ---

    # 1. Specific High-Ranking Feasts/Days
    name_lower = day_name.lower()
    if target_date == date(year, 1, 1) or "Mary, Mother of God" in day_name: return WHITE
    if target_date == date(year, 11, 1) or "All Saints" in day_name: return WHITE
    if target_date == date(year, 12, 8) or "Immaculate Conception" in day_name: return WHITE
    if target_date == date(year, 12, 25) or "Nativity of the Lord" in day_name or "Christmas" in day_name: return WHITE
    if target_date == date(year, 6, 24) or "Nativity of Saint John the Baptist" in day_name: return WHITE
    if target_date == date(year, 1, 25) or "Conversion of Saint Paul" in day_name: return WHITE
    if target_date == date(year, 2, 22) or "Chair of Saint Peter" in day_name: return WHITE
    if target_date == date(year, 12, 27) or (month == 12 and day == 27 and "Saint John" in day_name): return WHITE # Apostle & Evangelist -> Usually Red, but rule says White for this one
    if target_date == palm_sunday or "Palm Sunday" in day_name: return RED
    if target_date == good_friday or "Good Friday" in day_name: return RED
    if target_date == pentecost or "Pentecost" in day_name: return RED
    if "Trinity Sunday" in day_name or target_date == pentecost + relativedelta(weekday=SU(+1)): return WHITE
    
    # Check for keywords related to Red days AFTER specific feasts
    if "Passion of the Lord" in day_name: return RED
    if "Apostle" in day_name and "Saint John" not in day_name: return RED # Exception handled above
    if "Evangelist" in day_name and "Saint John" not in day_name: return RED
    if "Martyr" in day_name: return RED

    # Check for keywords related to White days (if not overridden by Red above)
    if " of the Lord" in name_lower and "passion" not in name_lower: return WHITE # Other Lord feasts
    if " Mary" in name_lower or "Our Lady" in name_lower or "Assumption" in name_lower: return WHITE
    if "Angel" in day_name: return WHITE
    # Saint check is tricky, could be Martyr (Red). Defaulting non-martyrs to White.
    if ("Saint" in day_name or "St." in day_name) and "Martyr" not in day_name and "Apostle" not in day_name and "Evangelist" not in day_name and "John" not in day_name: return WHITE
    
    # 2. Liturgical Seasons
    # Christmas Time (Dec 25 to Baptism of the Lord)
    if (month == 12 and day >= 25) or (month == 1 and target_date <= baptism_of_lord): return WHITE
    # Easter Time (Easter Sunday to Pentecost Sunday)
    if easter_date <= target_date <= pentecost: return WHITE
    # Lent (Ash Wednesday to Holy Thursday - approximate end before Easter)
    if ash_wednesday <= target_date < easter_date - timedelta(days=3): return VIOLET
    # Advent (First Sunday of Advent to Dec 24)
    if first_sunday_advent <= target_date <= date(year, 12, 24): return VIOLET

    # 3. Ordinary Time (Default)
    # Check if weekday falls within known Ordinary Time periods
    # Period 1: After Baptism of Lord until Ash Wednesday
    if baptism_of_lord < target_date < ash_wednesday: return GREEN
    # Period 2: After Pentecost until Advent starts
    if pentecost < target_date < first_sunday_advent: return GREEN
    
    # 4. Fallback/Default (Should ideally hit Ordinary Time Green)
    # Violet often used for Masses for the Dead if not specified
    if "Masses for the Dead" in day_name: return VIOLET # Or Black if preferred
     
    # Default to Green if no other rule applies
    return GREEN 


def scrape_day(target_date):
    """Scrapes the readings for a single day, attempting URL fallback."""
    date_str_url = target_date.strftime("%m%d%y")
    date_str_iso = target_date.strftime("%Y-%m-%d")
    url_cfm = f"{BASE_URL}{date_str_url}.cfm"
    url_nocfm = f"{BASE_URL}{date_str_url}" # Fallback URL

    # print(f"Attempting to scrape {date_str_iso} from {url_cfm}...") # Debug
    soup = get_soup(url_cfm)
    
    # --- URL FALLBACK LOGIC ---
    if soup is None:
        print(f"  -> Initial scrape failed for {date_str_iso}. Trying fallback URL: {url_nocfm}...")
        time.sleep(REQUEST_DELAY_SECONDS / 2) # Shorter delay before retry
        soup = get_soup(url_nocfm)
        if soup is None:
            print(f"  -> ERROR: Fallback scrape also failed for {date_str_iso}.")
            return None # Indicate complete failure for this date
    # --- END FALLBACK LOGIC ---

    data = {
        "date": date_str_iso, "name": None, "lectionary_number": None, "color": None,
        "reading_1": None, "reading_1_link": None, "psalm": None, "psalm_link": None,
        "allelulia": None, "allelulia_link": None, "reading_2": None, "reading_2_link": None,
        "gospel": None, "gospel_link": None,
    }

    # Extract Name from <title>
    title_tag = soup.find('title')
    if title_tag:
        title_text = title_tag.get_text(strip=True)
        data['name'] = title_text.split('|')[0].strip()

    # Determine Color (needs name first)
    data['color'] = get_liturgical_color(target_date, data['name'])

    # Extract Lectionary Number
    lectionary_container = soup.find('div', class_='b-lectionary')
    if lectionary_container:
        num_match = re.search(r'Lectionary:\s*(\d+)', lectionary_container.get_text())
        if num_match: data['lectionary_number'] = num_match.group(1).strip()

    # Extract Readings
    reading_blocks = soup.find_all('div', class_='b-verse')
    
    if not reading_blocks:
         print(f"  -> Warning: Could not find any reading blocks ('div.b-verse') for {date_str_iso}.")
    
    for block in reading_blocks:
        heading_tag = block.find('h3', class_='name')
        if not heading_tag: continue
        heading_text = heading_tag.get_text(strip=True)

        current_reading_type = None
        # --- Use regex to match Reading 1/I and 2/II ---
        if re.search(r'Reading\s+(1|I)\b', heading_text, re.IGNORECASE):
            current_reading_type = "reading_1"
        elif re.search(r'Responsorial\s+Psalm', heading_text, re.IGNORECASE):
            current_reading_type = "psalm"
        elif re.search(r'Reading\s+(2|II)\b', heading_text, re.IGNORECASE):
            current_reading_type = "reading_2"
        elif re.search(r'Alleluia|Gospel\s+Accl', heading_text, re.IGNORECASE):
            current_reading_type = "allelulia"
        elif re.search(r'Gospel\b', heading_text, re.IGNORECASE):
            current_reading_type = "gospel"

        if not current_reading_type: continue 

        address_div = block.find('div', class_='address')
        if not address_div: continue
            
        ref_link = address_div.find('a')
        if ref_link and ('/bible/' in ref_link.get('href', '') or 'usccb.org/bible' in ref_link.get('href','')): 
            ref_text = ref_link.get_text(strip=True)
            if data[current_reading_type] is None:
                 data[current_reading_type] = ref_text
                 link = parse_reference_to_link(ref_text)
                 data[f"{current_reading_type}_link"] = link
            
    return data

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    print("Starting USCCB readings scraper...")
    
    # --- LOAD EXISTING DATA ---
    existing_data = []
    existing_dates = set()
    if os.path.exists(OUTPUT_JSON):
        try:
            with open(OUTPUT_JSON, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            existing_dates = {item['date'] for item in existing_data if 'date' in item}
            print(f"Loaded {len(existing_dates)} existing dates from {OUTPUT_JSON}")
        except json.JSONDecodeError:
            print(f"Warning: Could not read existing data from {OUTPUT_JSON}. File might be corrupted.")
        except Exception as e:
            print(f"Warning: An error occurred loading existing data: {e}")
            
    all_data = existing_data # Start with existing data
    new_data_count = 0
    failed_dates = [] # List to track dates that failed scraping

    total_days = (END_DATE - START_DATE).days + 1
    current_day_num = 0

    for single_date in daterange(START_DATE, END_DATE):
        current_day_num += 1
        date_str_iso = single_date.strftime("%Y-%m-%d")
        
        # --- CHECK IF DATE ALREADY EXISTS ---
        if date_str_iso in existing_dates:
            # print(f"Skipping day {current_day_num}/{total_days}: {date_str_iso} (already exists)")
            continue
            
        print(f"Processing day {current_day_num}/{total_days}: {date_str_iso}")
        daily_data = scrape_day(single_date)
        
        if daily_data:
            all_data.append(daily_data)
            existing_dates.add(date_str_iso) # Add newly scraped date to set
            new_data_count += 1
        else:
            print(f"  -> Failed to scrape data for {date_str_iso}")
            failed_dates.append(date_str_iso) # Record failure
            
        time.sleep(REQUEST_DELAY_SECONDS)
        
    print(f"\nScraping complete. Added data for {new_data_count} new days.")
    
    # Sort data by date before writing
    all_data.sort(key=lambda x: x.get('date', ''))

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Ensured output directory exists: '{OUTPUT_DIR}'")
    
    print(f"Writing JSON data to {OUTPUT_JSON}...")
    try:
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        print("  -> JSON writing successful.")
    except Exception as e:
        print(f"  -> Error writing JSON file: {e}")
        
    print(f"Writing CSV data to {OUTPUT_CSV}...")
    try:
        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
            if all_data:
                # Dynamically get fieldnames from the first *complete* data entry
                # Find the first entry that has more than just the date key
                first_valid_entry = next((item for item in all_data if len(item) > 1), None)
                if first_valid_entry:
                    fieldnames = first_valid_entry.keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore') # Ignore extra fields if headers are inconsistent
                    writer.writeheader()
                    writer.writerows(all_data)
                    print("  -> CSV writing successful.")
                else:
                    print("  -> No valid data entries found to write to CSV.")
            else:
                 print("  -> No data to write to CSV.")
    except Exception as e:
        print(f"  -> Error writing CSV file: {e}")
        
    # --- Print Error Summary ---
    if failed_dates:
        print("\n--- Scraping Failure Summary ---")
        print("The script failed to retrieve data for the following dates:")
        for failed_date in failed_dates:
            print(f"  - {failed_date}")
        print("---------------------------------")
    # --- End Error Summary ---

    print("\n✅ Script finished.")

