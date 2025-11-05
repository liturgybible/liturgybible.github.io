# README

# What Bible do I need to bring to Mass? 

# For 2026-01-01 to 2026-12-31:
# 50.4% of dates from NT, Psalm, Gospel only (184 days)
# 46.8% of dates also include OT (171 days)
# 2.7% of dates also include deuterocanon (10 days)

# 50% of the time, a pocket NT + Psalms works 
# 47% of the tiem, a Bible with the OT is needed (Protestant Bible without the deuterocanon works)
# 3% of the time, a full Catholic Bible with the deuterocanon is needed


import os
import json
import csv
import re
from datetime import datetime
from dateutil.easter import easter # Required for liturgical date calculations
from dateutil.relativedelta import relativedelta, SU, TH # For finding Sundays, etc.

# --- CONFIGURATION ---

START_DATE = datetime(2026, 1, 1).date()
END_DATE = datetime(2026, 12, 31).date()

INPUT_JSON = "../data_usccb/usccb-readings.json"
OUTPUT_CSV = "lectionary_pct.csv" # Saves in the same /utils directory

# --- BOOK DEFINITIONS ---

# Master list of canonical book names
CATHOLIC_BIBLE_BOOKS_NAMES = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel",
    "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Tobit", "Judith", "Esther",
    "1 Maccabees", "2 Maccabees", "Job", "Psalms", "Proverbs", "Ecclesiastes", "Song of Songs", "Wisdom",
    "Sirach", "Isaiah", "Jeremiah", "Lamentations", "Baruch", "Ezekiel", "Daniel", "Hosea", "Joel",
    "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
    "Matthew", "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians", "2 Corinthians", "Galatians",
    "Ephesians", "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians", "1 Timothy", "2 Timothy", "Titus",
    "Philemon", "Hebrews", "James", "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation"
]

# Abbreviations map, normalized to the names above
BOOK_NAME_MAP = {
    "gen": "Genesis", "exod": "Exodus", "lev": "Leviticus", "num": "Numbers", "deut": "Deuteronomy",
    "josh": "Joshua", "judg": "Judges", "ruth": "Ruth", "1 sam": "1 Samuel", "2 sam": "2 Samuel",
    "1 kgs": "1 Kings", "2 kgs": "2 Kings", "1 chr": "1 Chronicles", "2 chr": "2 Chronicles",
    "ezra": "Ezra", "neh": "Nehemiah", "tob": "Tobit", "jdt": "Judith", "esth": "Esther",
    "1 macc": "1 Maccabees", "2 macc": "2 Maccabees", "job": "Job", "ps": "Psalms", "prov": "Proverbs",
    "eccl": "Ecclesiastes", "song": "Song of Songs", "wis": "Wisdom", "sir": "Sirach",
    "isa": "Isaiah", "jer": "Jeremiah", "lam": "Lamentations", "bar": "Baruch", "ezek": "Ezekiel",
    "dan": "Daniel", "hos": "Hosea", "joel": "Joel", "amos": "Amos", "obad": "Obadiah",
    "jonah": "Jonah", "mic": "Micah", "nah": "Nahum", "hab": "Habakkuk", "zeph": "Zephaniah",
    "hag": "Haggai", "zech": "Zechariah", "mal": "Malachi", "matt": "Matthew", "mark": "Mark",
    "luke": "Luke", "john": "John", "acts": "Acts", "rom": "Romans", "1 cor": "1 Corinthians",
    "2 cor": "2 Corinthians", "gal": "Galatians", "eph": "Ephesians", "phil": "Philippians",
    "col": "Colossians", "1 thess": "1 Thessalonians", "2 thess": "2 Thessalonians", "1 tim": "1 Timothy",
    "2 tim": "2 Timothy", "titus": "Titus", "phlm": "Philemon", "heb": "Hebrews", "jas": "James",
    "1 pet": "1 Peter", "2 pet": "2 Peter", "1 john": "1 John", "2 john": "2 John",
    "3 john": "3 John", "jud": "jude", "rv": "revelation", "psalm": "Psalms"
}
# Add full names to the map as well for easy lookup
for name in CATHOLIC_BIBLE_BOOKS_NAMES:
    BOOK_NAME_MAP[name.lower()] = name
    
# Sort keys by length, descending, to match "1 Sam" before "Sam"
SORTED_BOOK_KEYS = sorted(BOOK_NAME_MAP.keys(), key=len, reverse=True)

# --- Define Book Categories ---
DEUTEROCANONICAL_BOOKS = [
    "Tobit", "Judith", "1 Maccabees", "2 Maccabees", "Wisdom", "Sirach", "Baruch"
]

# Define the deuterocanonical *parts* of Esther and Daniel
# Format: "BookName": [ (chapter, start_verse, end_verse), ... ]
DEUTEROCANONICAL_PARTS = {
    "Daniel": [
        (3, 24, 90),  # Prayer of Azariah / Song of the Three Children
        (13, 1, 999), # Chapter 13 (Susanna)
        (14, 1, 999)  # Chapter 14 (Bel and the Dragon)
    ],
    "Esther": [
        (10, 4, 999)  # Protestant Esther ends at 10:3. Anything from 10:4 onward is DC.
    ]
    # Note: USCCB numbering for Esther (e.g., C:12-17) is different from the
    # KJV/DRA numbering (e.g., 12:12-17). We assume the ref_string uses
    # standard chapter/verse numbers. Esther 10:4+ covers all additions.
}

PSALM_BOOK = ["Psalms"]
NEW_TESTAMENT_BOOKS = []
OLD_TESTAMENT_BOOKS = [] # Protocanon (OT - DC)

is_nt = False
for book in CATHOLIC_BIBLE_BOOKS_NAMES:
    if book == "Matthew":
        is_nt = True
    
    if is_nt:
        NEW_TESTAMENT_BOOKS.append(book)
    elif book not in DEUTEROCANONICAL_BOOKS and book not in PSALM_BOOK:
        OLD_TESTAMENT_BOOKS.append(book)

# Create a master lookup for categorization
BOOK_CATEGORIES = {}
for book in OLD_TESTAMENT_BOOKS: BOOK_CATEGORIES[book] = "OT"
for book in DEUTEROCANONICAL_BOOKS: BOOK_CATEGORIES[book] = "DC" # This category is now partially redundant
for book in PSALM_BOOK: BOOK_CATEGORIES[book] = "Psalm"
for book in NEW_TESTAMENT_BOOKS: BOOK_CATEGORIES[book] = "NT" # Includes Gospels

# --- HELPER FUNCTIONS ---

def parse_book_from_ref(ref_string):
    """
    Parses a reference string and returns the normalized book name
    and the rest of the string (chapter/verse part).
    Returns (book_name, rest_of_string, error_message).
    """
    if not ref_string:
        return None, None, "No reference string"
        
    normalized_str = ref_string.strip().replace('NABRE', '')

    for key in SORTED_BOOK_KEYS:
        # Use regex to find the book name as a whole word
        pattern = r'\b' + re.escape(key) + r'\b'
        match = re.search(pattern, normalized_str, re.IGNORECASE)
        if match:
            # Check if what follows is a chapter number
            rest = normalized_str[match.end():].strip()
            if re.match(r'^\d', rest):
                return BOOK_NAME_MAP[key], rest, None # Success
    
    return None, None, f"Could not find a known book in '{ref_string}'"

def is_deuterocanonical(book_name, rest_of_string, dc_books, dc_parts):
    """
    Checks if a reading is deuterocanonical, either by book or by part.
    """
    if not book_name or not rest_of_string:
        return False
        
    # 1. Check if the *entire book* is deuterocanonical
    if book_name in dc_books:
        return True
        
    # 2. Check if the book is one that has deuterocanonical *parts*
    if book_name in dc_parts:
        dc_ranges = dc_parts[book_name]
        
        # Extract all simple chapter:verse points from the string
        # e.g., "3:52-90" -> [('3', '52')]
        # e.g., "13:1, 5-9" -> [('13', '1'), ('13', '5')]
        # This is a simple check, but effective. It checks the *start* of any range.
        verse_points = re.findall(r'(\d+):(\d+)', rest_of_string)
        
        if not verse_points:
             # Handle references with no chapter, e.g. "Esther 11, 12" -> "11", "12"
             # This is a simplified check for full DC chapters
             if book_name == "Daniel" and (re.search(r'\b13\b', rest_of_string) or re.search(r'\b14\b', rest_of_string)):
                 return True
             if book_name == "Esther" and (re.search(r'\b11\b|\b12\b|\b13\b|\b14\b|\b15\b|\b16\b', rest_of_string)):
                 return True
             return False # No chapter:verse points found

        for chap_str, verse_str in verse_points:
            try:
                chap_num = int(chap_str)
                verse_num = int(verse_str)
                
                # Check if this point falls into any DC range for that book
                for dc_range in dc_ranges:
                    if (chap_num == dc_range[0] and 
                        verse_num >= dc_range[1] and 
                        verse_num <= dc_range[2]):
                        return True
            except ValueError:
                continue # Should not happen with regex, but good to be safe
                
    return False

def get_day_label(day_data, book_categories, dc_books, dc_parts):
    """
    Analyzes a day's readings and returns a label and the triggering reading.
    Returns (label, reading_string)
    """
    
    reading_keys = ["reading_1", "reading_2", "psalm", "allelulia", "gospel"]
    has_dc = False
    has_ot = False
    only_nt_psalm_gospel = True # Assume true until proven otherwise
    
    first_dc_reading = None
    first_ot_reading = None

    for key in reading_keys:
        ref_string = day_data.get(key)
        if not ref_string:
            continue # Skip empty readings
            
        book_name, rest_of_string, error = parse_book_from_ref(ref_string)
        if error:
            # print(f"  -> Warning (Date: {day_data['date']}): {error}")
            continue # Skip unparseable references (e.g., "See Ritual Mass")

        # --- UPDATED LOGIC: Check DC first and store the reading ---
        if is_deuterocanonical(book_name, rest_of_string, dc_books, dc_parts):
            has_dc = True
            only_nt_psalm_gospel = False
            if first_dc_reading is None:
                first_dc_reading = ref_string
        else:
            # If not DC, check its protocanonical category
            category = book_categories.get(book_name)
            if category == "OT":
                has_ot = True
                only_nt_psalm_gospel = False
                if first_ot_reading is None:
                    first_ot_reading = ref_string
            elif category in ["NT", "Psalm"]:
                pass # This is expected for the NT-only case
            else:
                print(f"  -> Warning (Date: {day_data['date']}): Book '{book_name}' not categorized.")
                only_nt_psalm_gospel = False

    # Return label based on priority
    if has_dc:
        return "includes DC", first_dc_reading
    if has_ot:
        return "includes OT", first_ot_reading
    if only_nt_psalm_gospel:
        return "NT, Psalm, Gospel", None
    
    # This can happen if a day only has uncategorized readings
    return "Other", None

# --- MAIN EXECUTION ---

if __name__ == "__main__":
    print(f"Starting lectionary analysis for {START_DATE} to {END_DATE}...")
    
    if not os.path.exists(INPUT_JSON):
        print(f"FATAL ERROR: Input file '{INPUT_JSON}' not found.")
        exit()
    
    all_data_to_write = []
    label_counts = {
        "includes DC": 0,
        "includes OT": 0,
        "NT, Psalm, Gospel": 0,
        "Other": 0
    }
    total_days_processed = 0

    try:
        with open(INPUT_JSON, 'r', encoding='utf-8') as f:
            all_readings_data = json.load(f)
    except json.JSONDecodeError:
        print(f"FATAL ERROR: Could not parse {INPUT_JSON}. File may be corrupt.")
        exit()

    print(f"Loaded {len(all_readings_data)} days from JSON.")

    for day_data in all_readings_data:
        try:
            current_date = datetime.strptime(day_data['date'], '%Y-%m-%d').date()
        except ValueError:
            print(f"  -> Skipping row with invalid date format: {day_data.get('date')}")
            continue
            
        if START_DATE <= current_date <= END_DATE:
            total_days_processed += 1
            # --- UPDATED: Capture both return values ---
            label, reading = get_day_label(day_data, BOOK_CATEGORIES, DEUTEROCANONICAL_BOOKS, DEUTEROCANONICAL_PARTS)
            
            if label:
                label_counts[label] += 1
                # --- UPDATED: Add 'reading' to the output dictionary ---
                all_data_to_write.append({"date": day_data['date'], "label": label, "reading": reading})
            else:
                 print(f"  -> Warning: No label generated for {day_data['date']}")
                 label_counts["Other"] += 1
                 all_data_to_write.append({"date": day_data['date'], "label": "Other", "reading": None})


    # --- Print Stats ---
    print("\n--- Analysis Complete ---")
    if total_days_processed > 0:
        pct_dc = (label_counts["includes DC"] / total_days_processed) * 100
        pct_ot = (label_counts["includes OT"] / total_days_processed) * 100
        pct_nt = (label_counts["NT, Psalm, Gospel"] / total_days_processed) * 100
        
        print(f"Total days processed: {total_days_processed}")
        print(f"\n{pct_nt:0.1f}% of dates from NT, Psalm, Gospel only ({label_counts['NT, Psalm, Gospel']} days)")
        print(f"{pct_ot:0.1f}% of dates also include OT ({label_counts['includes OT']} days)")
        print(f"{pct_dc:0.1f}% of dates also include deuterocanon ({label_counts['includes DC']} days)")
    else:
        print("No data found for the specified date range.")

    # --- Write CSV File ---
    print(f"\nWriting analysis to {OUTPUT_CSV}...")
    try:
        with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
            if all_data_to_write:
                # --- UPDATED: Add 'reading' to fieldnames ---
                writer = csv.DictWriter(f, fieldnames=["date", "label", "reading"])
                writer.writeheader()
                writer.writerows(all_data_to_write)
                print("  -> CSV writing successful.")
            else:
                 print("  -> No data to write to CSV.")
    except Exception as e:
        print(f"  -> Error writing CSV file: {e}")

    print("\n✅ Script finished.")