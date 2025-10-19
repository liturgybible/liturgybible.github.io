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
    "Weekday Readings": "#B35C58",
    "LOTH: OR": "#4C6B4F",
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

# --- PARSING LOGIC ---

def parse_reading_string(reading_str):
    """
    Parses a complex scripture reference string into a book name and a list of segments.
    Returns (book_name, segments, error_message).
    """
    # Normalize different types of dashes (em-dash, en-dash) to a standard hyphen.
    normalized_str = reading_str.strip().replace('—', '-').replace('–', '-')

    # Find the book name - everything up to the first digit.
    match = re.match(r'^((\d\s)?[A-Za-z\s]+)\s*(\d.*)', normalized_str)
    if not match:
        return None, None, f"Could not extract book name from '{reading_str}'"
    
    book_abbr = match.group(1).strip()
    rest_of_string = match.group(3)
    
    # Normalize book name
    book_name = None
    for key, value in BOOK_NAME_MAP.items():
        if book_abbr.lower() == key.lower():
            book_name = value
            break
    if not book_name:
        # If not in map, check for full name match
        for key, value in BOOK_NAME_MAP.items():
             if book_abbr.lower() == value.lower():
                 book_name = value
                 break
    if not book_name:
        return None, None, f"Book abbreviation '{book_abbr}' not found in map."

    segments = []
    last_chapter = None
    
    # Split by common delimiters for multiple parts
    parts = re.split(r'[,;]', rest_of_string)

    for part in parts:
        part = part.strip()
        if not part: continue

        full_ref = part
        if ':' not in part:
            if not last_chapter:
                return None, None, f"Reference part '{part}' has no chapter and no previous chapter was established."
            full_ref = f"{last_chapter}:{part}"
        
        # Extract chapter from the full reference
        try:
            current_chapter = full_ref.split(':')[0].strip()
            last_chapter = current_chapter
        except IndexError:
             return None, None, f"Could not parse chapter from '{full_ref}'"

        # Check for a range (e.g., 10-14 or 1-2a)
        if '-' in full_ref:
            try:
                # Special handling for ranges that cross chapters, e.g., "1:1-2:2"
                if ':' in full_ref.split('-', 1)[1]:
                     start_part, end_part = full_ref.split('-', 1)
                else: # Standard range within a chapter, e.g., "1:10-14"
                    start_part, end_part = full_ref.rsplit('-', 1)

                start = start_part.strip()
                end = end_part.strip()

                # If end part is just a verse or verse-part, prepend the chapter
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
            row_num = i + 2 # Account for header row
            
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
            
            book_from_first_part = None
            if reading_options:
                first_part_match = re.match(r'^((\d\s)?[A-Za-z\s]+)\s*', reading_options[0])
                if first_part_match:
                    book_from_first_part = first_part_match.group(1).strip()
                else:
                    print(f"Warning (Row {row_num}): Could not determine book from first part of reading '{reading_options[0]}'. Skipping row.")
                    continue

            for reading_part in reading_options:
                
                full_reading_part = reading_part
                if book_from_first_part and re.match(r'^\d', reading_part):
                    full_reading_part = f"{book_from_first_part} {reading_part}"

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
                elif len(segments) == 1 and segments[0]['start'] != segments[0]['end']:
                    reading_obj["start"] = segments[0]['start']
                    reading_obj["end"] = segments[0]['end']
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

