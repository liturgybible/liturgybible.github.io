# Data sourced from https://catholic-resources.org/ with the permission of Fr. Felix Just, S.J.
# Gsheet data prep: https://docs.google.com/spreadsheets/d/1GB48rM6wN8Ghrj4Hfggb8WEqDi64d9VOiZO0uTUddRs/edit?usp=sharing

import os
import csv
import json
import re

# --- CONFIGURATION ---

INPUT_CSV = "liturgy_bible_data.csv"
OUTPUT_DIR = "data/"

# Color mapping
COLOR_MAP = {
    "Sunday Reading": "#7B2E2B",
    "Solemnities & Feasts": "#C9A441",
    "Weekday Reading": "#B35C58",
    "LOTH: OR": "#4C6B4F",
    "LOTH: Psalms": "#5E4B81",
    "LOTH: Ordinary": "#5E4B81",
    "LOTH: Other": "#4A628A"
}
DEFAULT_COLOR = "#808080" # Grey for any unmapped colors

# Mapping of book names from the CSV to the canonical name used for filenames/grouping
BOOK_NAME_MAP = {
    "Gen": "Genesis", "Exod": "Exodus", "Lev": "Leviticus", "Num": "Numbers", "Deut": "Deuteronomy",
    "Josh": "Joshua", "Judg": "Judges", "Ruth": "Ruth", "1 Sam": "1 Samuel", "2 Sam": "2 Samuel",
    "1 Kgs": "1 Kings", "2 Kgs": "2 Kings", "1 Chr": "1 Chronicles", "2 Chr": "2 Chronicles",
    "Ezra": "Ezra", "Neh": "Nehemiah", "Tob": "Tobit", "Jdt": "Judith", "Est": "Esther",
    "1 Macc": "1 Maccabees", "2 Macc": "2 Maccabees", "Job": "Job", "Ps": "Psalms", "Prov": "Proverbs",
    "Eccl": "Ecclesiastes", "Song": "Song of Songs", "Wis": "Wisdom", "Sir": "Sirach",
    "Isa": "Isaiah", "Jer": "Jeremiah", "Lam": "Lamentations", "Bar": "Baruch", "Ezek": "Ezekiel",
    "Dan": "Daniel", "Hos": "Hosea", "Joel": "Joel", "Amos": "Amos", "Obad": "Obadiah",
    "Jonah": "Jonah", "Mic": "Micah", "Nah": "Nahum", "Hab": "Habakkuk", "Zeph": "Zephaniah",
    "Hag": "Haggai", "Zech": "Zechariah", "Mal": "Malachi", "Matt": "Matthew", "Mark": "Mark",
    "Luke": "Luke", "John": "John", "Acts": "Acts", "Rom": "Romans", "1 Cor": "1 Corinthians",
    "2 Cor": "2 Corinthians", "Gal": "Galatians", "Eph": "Ephesians", "Phil": "Philippians",
    "Col": "Colossians", "1 Thess": "1 Thessalonians", "2 Thess": "2 Thessalonians", "1 Tim": "1 Timothy",
    "2 Tim": "2 Timothy", "Titus": "Titus", "Phlm": "Philemon", "Heb": "Hebrews", "Jas": "James",
    "1 Pet": "1 Peter", "2 Pet": "2 Peter", "1 John": "1 John", "2 John": "2 John",
    "3 John": "3 John", "Jude": "Jude", "Rev": "Revelation"
}
# Also add full names to the map so they can be found
for name in list(BOOK_NAME_MAP.values()):
    if name not in BOOK_NAME_MAP:
        BOOK_NAME_MAP[name] = name

# Sort keys by length, descending, to match longer names first (e.g., "1 Sam" before "Sam")
SORTED_BOOK_KEYS = sorted(BOOK_NAME_MAP.keys(), key=len, reverse=True)


# --- PARSING LOGIC ---

def parse_reading_string(reading_str):
    """
    Parses a complex scripture reference string by finding a known book name within it.
    Returns (book_name, segments, error_message).
    """
    normalized_str = reading_str.strip().replace('—', '-').replace('–', '-')

    book_name = None
    rest_of_string = None

    # Iterate through sorted book keys to find the correct one in the string
    for book_abbr in SORTED_BOOK_KEYS:
        # Use regex to find the book name as a whole word
        pattern = r'\b' + re.escape(book_abbr) + r'\b'
        match = re.search(pattern, normalized_str, re.IGNORECASE)
        if match:
            book_name = BOOK_NAME_MAP[book_abbr]
            rest_of_string = normalized_str[match.end():].strip()
            # Ensure the part that follows starts with a digit
            if re.match(r'^\d', rest_of_string):
                break # We found a valid match
            else: # False positive, continue searching
                book_name = None


    if not book_name or rest_of_string is None:
        return None, None, f"Could not extract a valid book and chapter from '{reading_str}'"

    segments = []
    last_chapter = None
    
    parts = re.split(r'[,;]', rest_of_string)

    for part in parts:
        part = part.strip()
        if not part: continue

        full_ref = part
        if ':' not in part:
            if not last_chapter:
                return None, None, f"Reference part '{part}' has no chapter and no previous one was set."
            full_ref = f"{last_chapter}:{part}"
        
        current_chapter = full_ref.split(':')[0].strip()
        last_chapter = current_chapter

        if '-' in full_ref:
            try:
                start_part, end_part = full_ref.split('-', 1)
                start = start_part.strip()
                end = end_part.strip()

                if ':' not in end:
                    end = f"{current_chapter}:{end}"
                segments.append({'start': start, 'end': end})
            except ValueError:
                return None, None, f"Could not parse range from '{full_ref}'"
        else: # It's a single verse
            segments.append({'start': full_ref, 'end': full_ref})

    return book_name, segments, None

# --- MAIN EXECUTION ---

if __name__ == "__main__":
    print("Starting data generation from CSV...")
    
    if not os.path.exists(INPUT_CSV):
        print(f"FATAL ERROR: Input file '{INPUT_CSV}' not found. Please place it in the same directory as the script.")
        exit()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    all_bible_data = {}

    with open(INPUT_CSV, mode='r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        for i, row in enumerate(reader):
            row_num = i + 2 
            
            liturgy = row.get("Liturgy", "").strip()
            name = row.get("Name", "").strip()
            reading_str = row.get("Reading", "").strip()
            color_map_key = row.get("Color Map", "").strip()
            lectionary_num = row.get("Lectionary #", "").strip()
            year = row.get("Year", "").strip()

            if not reading_str:
                print(f"Warning (Row {row_num}): 'Reading' column is empty. Skipping row.")
                continue

            reading_options = [r.strip() for r in reading_str.split(" or ")]
            
            # --- FIX IS HERE ---
            book_abbr_from_first_part = None
            if len(reading_options) > 1:
                first_part_str = reading_options[0]
                # Find the book abbreviation used in the first part of the reading.
                for book_abbr in SORTED_BOOK_KEYS:
                    pattern = r'\b' + re.escape(book_abbr) + r'\b'
                    match = re.search(pattern, first_part_str, re.IGNORECASE)
                    if match:
                        # Check that what follows is a chapter number to confirm it's a real match
                        rest = first_part_str[match.end():].strip()
                        if re.match(r'^\d', rest):
                            book_abbr_from_first_part = match.group(0) # Get the exact matched string (e.g., "Gen")
                            break
                if not book_abbr_from_first_part:
                    print(f"Warning (Row {row_num}): Could not determine book from first part of 'or' reading: '{first_part_str}'")

            for index, reading_part in enumerate(reading_options):
                
                full_reading_part = reading_part
                # If this is a subsequent part of an "or" clause and it starts with a number,
                # it's missing the book name. Prepend the one we found earlier.
                if index > 0 and book_abbr_from_first_part and re.match(r'^\d', reading_part):
                    full_reading_part = f"{book_abbr_from_first_part} {reading_part}"

                book, segments, error = parse_reading_string(full_reading_part)
                if error:
                    print(f"Warning (Row {row_num}): {error} in reading part '{full_reading_part}'")
                    continue
                    
                final_name = name
                details = []
                if year: details.append(year)
                if lectionary_num: details.append(f"#{lectionary_num}")
                if details:
                    final_name += f" [{', '.join(details)}]"
                
                if len(reading_options) > 1 and reading_part != reading_options[0]:
                    final_name += " (short)"

                color = COLOR_MAP.get(color_map_key)
                if not color:
                    print(f"Warning (Row {row_num}): Color Map '{color_map_key}' not found. Using default.")
                    color = DEFAULT_COLOR

                reading_obj = {"name": final_name, "color": color}
                if len(segments) > 1:
                    reading_obj["segments"] = segments
                elif segments:
                    reading_obj["start"] = segments[0]['start']
                    reading_obj["end"] = segments[0]['end']
                else:
                     print(f"Warning (Row {row_num}): No segments parsed from '{reading_part}'. Skipping.")
                     continue

                if book not in all_bible_data:
                    all_bible_data[book] = {"lectionaryReadings": [], "divineOffice": []}

                if liturgy == "Lectionary":
                    all_bible_data[book]["lectionaryReadings"].append(reading_obj)
                elif liturgy == "Divine Office":
                    all_bible_data[book]["divineOffice"].append(reading_obj)
                else:
                    print(f"Warning (Row {row_num}): Unknown 'Liturgy' type '{liturgy}'. Skipping row.")

    print("\n--- Writing JSON files ---")
    for book, data in all_bible_data.items():
        filename = book.lower().replace(" ", "-") + ".json"
        filepath = os.path.join(OUTPUT_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2)
        print(f"  -> Saved {filepath}")

    print("\n✅ Data generation complete.")

