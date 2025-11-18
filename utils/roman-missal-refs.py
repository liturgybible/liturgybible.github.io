#!/usr/bin/env python3

"""
This script reads a CSV file of Roman Missal references
(utils/roman-missal-refs.csv) and converts it into the
JSON format required by liturgybible.org.

This script is for Step 2 of the plan.
"""

import csv
import json
import os
import re

# Input CSV file (must be in the same directory)
INPUT_FILE = "roman-missal-refs.csv"

# The output directory and file
OUTPUT_DIR = "../data/roman-missal-refs"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "roman-missal-refs.json")

# A mapping of book names (from the CSV) to the slugs used in liturgybible.org
# This is based on the BOOK_SLUG_MAP_JS from your script.js
BOOK_SLUG_MAP = {
    # OT - Pentateuch
    "gen": "genesis", "gn": "genesis",
    "ex": "exodus",
    "lev": "leviticus", "lv": "leviticus",
    "num": "numbers", "nm": "numbers",
    "deut": "deuteronomy", "dt": "deuteronomy",
    
    # OT - Historical
    "josh": "joshua",
    "judg": "judges",
    "ruth": "ruth",
    "1 sam": "1-samuel",
    "2 sam": "2-samuel",
    "1 kgs": "1-kings",
    "2 kgs": "2-kings",
    "1 chr": "1-chronicles",
    "2 chr": "2-chronicles",
    "ezra": "ezra",
    "neh": "nehemiah",
    "tob": "tobit",
    "jud": "judith", "jdt": "judith",
    "esth": "esther",
    "1 macc": "1-maccabees",
    "2 macc": "2-maccabees",

    # OT - Wisdom
    "job": "job",
    "ps": "psalms", "psalm": "psalms",
    "prov": "proverbs",
    "eccl": "ecclesiastes",
    "song": "song-of-songs",
    "wis": "wisdom",
    "sir": "sirach",

    # OT - Prophets
    "isa": "isaiah",
    "jer": "jeremiah",
    "lam": "lamentations",
    "bar": "baruch",
    "ezek": "ezekiel",
    "dan": "daniel",
    "hos": "hosea",
    "joel": "joel",
    "amos": "amos",
    "obad": "obadiah",
    "jonah": "jonah",
    "mic": "micah",
    "nah": "nahum",
    "hab": "habakkuk",
    "zeph": "zephaniah",
    "hag": "haggai",
    "zech": "zechariah",
    "mal": "malachi",

    # NT - Gospels
    "matt": "matthew", "mt": "matthew",
    "mark": "mark", "mk": "mark",
    "luke": "luke", "lk": "luke",
    "john": "john", "jn": "john",

    # NT - Acts, Epistles, Rev
    "acts": "acts",
    "rom": "romans",
    "1 cor": "1-corinthians",
    "2 cor": "2-corinthians",
    "gal": "galatians",
    "eph": "ephesians",
    "phil": "philippians",
    "col": "colossians",
    "1 thess": "1-thessalonians",
    "2 thess": "2-thessalonians",
    "1 tim": "1-timothy",
    "2 tim": "2-timothy",
    "titus": "titus",
    "philem": "philemon",
    "heb": "hebrews",
    "jas": "james",
    "1 pet": "1-peter",
    "2 pet": "2-peter",
    "1 john": "1-john",
    "2 john": "2-john",
    "3 john": "3-john",
    "jude": "jude",
    "rev": "revelation",
}

def parse_scripture_ref(ref_string, line_num):
    """
    Parses a scripture reference string (e.g., "Matt. 28:19")
    Returns (book_slug, chapter, verse) or None
    """
    # Regex:
    # ^\s* - Start of string, optional whitespace
    # ([\d\sA-Za-z]+) - Capture group 1: The book name (e.g., "Matt", "1 Chr")
    # \.?           - Optional period (e.g., "Matt.")
    # \s+           - One or more spaces
    # (\d+)         - Capture group 2: The chapter number
    # :             - A literal colon
    # (\d+)         - Capture group 3: The (start) verse number
    # .* - Allow for ranges (e.g., ":19-20") or other text
    match = re.match(r'^\s*([\d\sA-Za-z]+)\.?\s+(\d+):(\d+).*', ref_string.strip())
    
    if not match:
        print(f"Warning [Line {line_num}]: Could not parse reference: '{ref_string}'")
        return None

    book_name_raw = match.group(1).lower().strip()
    chapter = match.group(2)
    verse = match.group(3)

    # Find the longest matching key
    # (e.g., "1 chr" should match before "1")
    book_slug = None
    
    # Check for exact match first
    if book_name_raw in BOOK_SLUG_MAP:
        book_slug = BOOK_SLUG_MAP[book_name_raw]
    else:
        # Check for partial match (e.g., "1 corinthians" -> "1 cor")
        for key in sorted(BOOK_SLUG_MAP.keys(), key=len, reverse=True):
            if book_name_raw.startswith(key):
                book_slug = BOOK_SLUG_MAP[key]
                break

    if not book_slug:
        print(f"Warning [Line {line_num}]: No slug found for book: '{book_name_raw}' (from ref: '{ref_string}')")
        return None
        
    return (book_slug, chapter, verse)

def convert_csv_to_json():
    """
    Reads the CSV and builds the JSON data structure.
    """
    print(f"Opening {INPUT_FILE}...")
    
    all_refs = {}
    
    try:
        with open(INPUT_FILE, mode='r', encoding='utf-8') as f:
            
            # --- START NEW FIX ---
            # 1. Detect the delimiter (comma vs. tab)
            try:
                # Read a sample to detect dialect
                sample = f.read(2048)
                dialect = csv.Sniffer().sniff(sample)
                print(f"Detected CSV dialect: Delimiter='{dialect.delimiter}'")
                f.seek(0) # Go back to the start
            except csv.Error:
                print("Warning: Could not auto-detect CSV dialect. Assuming comma-separated.")
                dialect = 'excel' # Default
            
            # 2. Read headers manually to clean them
            reader = csv.reader(f, dialect)
            try:
                headers_raw = next(reader)
            except StopIteration:
                print("Error: CSV file is empty.")
                return

            headers = [h.strip() for h in headers_raw]
            print(f"Detected headers: {headers}")

            # 3. Find the correct header names
            # Find the first header that contains "roman missal" (case-insensitive)
            rm_header = next((h for h in headers if 'roman missal' in h.lower()), None)
            # Find the first header that contains "scripture reference" (case-insensitive)
            ref_header = next((h for h in headers if 'scripture reference' in h.lower()), None)

            if not rm_header or not ref_header:
                print(f"Error: Could not find required headers in {headers}.")
                print(f"  Looking for 'Roman Missal', found: {rm_header}")
                print(f"  Looking for 'Scripture Reference', found: {ref_header}")
                print(f"  Please ensure {INPUT_FILE} has the correct headers.")
                return

            print(f"Using header '{rm_header}' for Missal ID.")
            print(f"Using header '{ref_header}' for Scripture Reference.")

            # 4. Create DictReader, passing in our *cleaned* header names
            # We already skipped the header, so we create the reader on the rest of the file
            dict_reader = csv.DictReader(f, fieldnames=headers, dialect=dialect)
            # --- END NEW FIX ---
            
            for i, row in enumerate(dict_reader):
                # We use the *original* raw headers to get the data,
                # since DictReader maps them.
                rm_header_raw = headers_raw[headers.index(rm_header)]
                ref_header_raw = headers_raw[headers.index(ref_header)]

                rm_id = row.get(rm_header_raw)
                ref_string = row.get(ref_header_raw)
                
                # More detailed logging for the "empty row" check
                if not rm_id or not ref_string:
                    print(f"Warning: Skipping empty or invalid row {i+2}.")
                    print(f"  - Raw data: {row}")
                    print(f"  - Found RM ID: '{rm_id}'")
                    print(f"  - Found Ref: '{ref_string}'")
                    continue
                
                rm_id = rm_id.strip()
                ref_string = ref_string.strip()
                
                parsed = parse_scripture_ref(ref_string, i+2) # Pass row number
                
                if parsed:
                    book_slug, chapter, verse = parsed
                    
                    # Ensure path exists
                    all_refs.setdefault(book_slug, {}).setdefault(chapter, {}).setdefault(verse, [])
                    
                    # Add the reference if not already present
                    if rm_id not in all_refs[book_slug][chapter][verse]:
                        all_refs[book_slug][chapter][verse].append(rm_id)

    except FileNotFoundError:
        print(f"Error: Could not find file: {INPUT_FILE}")
        print("Please create this file in the 'utils/' directory with headers: Roman Missal,Scripture Reference")
        return
    except Exception as e:
        print(f"An error occurred: {e}")
        return

    if not all_refs:
        print("No valid references were processed from the CSV.")
        return

    # 5. Write to JSON file
    print(f"Writing {len(all_refs)} books to {OUTPUT_FILE}...")
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            # Sort keys for consistent output
            json.dump(all_refs, f, indent=2, sort_keys=True)
            
        print("Done.")
        print(f"Successfully created {OUTPUT_FILE}")
        
    except IOError as e:
        print(f"Error: Could not write file: {e}")

if __name__ == "__main__":
    convert_csv_to_json()