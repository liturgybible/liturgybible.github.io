#!/usr/bin/env python3

"""
Parses USCCB readings for a specific date range and 
calculates the coverage of CCC (Catechism of the Catholic Church) 
paragraphs referenced by those readings.

Assumes this script is in a 'utils' directory and data files are in
'../data_usccb/' and '../data/ccc-refs/'.
"""

import json
import os
import re
from typing import Set, Dict, Optional, Tuple, List, Any

# --- Constants ---

# Get the directory of this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Get the project root directory (assuming script is in 'utils/')
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..'))

# Paths relative to the project root
READINGS_FILE = os.path.join(PROJECT_ROOT, 'data_usccb', 'usccb-readings.json')
CCC_REFS_DIR = os.path.join(PROJECT_ROOT, 'data', 'ccc-refs')

START_DATE = '2026-01-01'
END_DATE = '2026-12-31'
TOTAL_CCC_PARAGRAPHS = 2865

# Section bounds (inclusive)
SECTION_1_BOUNDS = (1, 1065)
SECTION_2_BOUNDS = (1066, 1690)
SECTION_3_BOUNDS = (1691, 2557)
SECTION_4_BOUNDS = (2558, 2865)

# Section totals
SECTION_1_TOTAL = SECTION_1_BOUNDS[1] - SECTION_1_BOUNDS[0] + 1 # 1065
SECTION_2_TOTAL = SECTION_2_BOUNDS[1] - SECTION_2_BOUNDS[0] + 1 # 625
SECTION_3_TOTAL = SECTION_3_BOUNDS[1] - SECTION_3_BOUNDS[0] + 1 # 867
SECTION_4_TOTAL = SECTION_4_BOUNDS[1] - SECTION_4_BOUNDS[0] + 1 # 308

# Regex to capture book, chapter, and verse parts
# e.g., "1 Corinthians 15:3-5, 8"
# Group 1: Book name (non-greedy)
# Group 2: Chapter (digits)
# Group 3: Verse part (digits, commas, hyphens)
CITATION_REGEX = re.compile(r'^(.*?)\s+(\d+):([\d,-]+)$')

# Type hint for the CCC ref cache
CccRefCache = Dict[str, Optional[Dict[str, Any]]]

# --- Helper Functions ---

def parse_verses(verse_part: str) -> Set[int]:
    """
    Converts a verse string like "2-3, 5, 6, 8" into a set of integers.
    """
    verses: Set[int] = set()
    try:
        parts = verse_part.split(',')
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if '-' in part:
                # Handle verse range, e.g., "16-21"
                start_str, end_str = part.split('-')
                start = int(start_str.strip())
                end = int(end_str.strip())
                if start > end:
                    start, end = end, start # Handle reverse order if any
                verses.update(range(start, end + 1))
            elif part.isdigit():
                # Handle single verse, e.g., "5"
                verses.add(int(part))
    except ValueError as e:
        print(f"Warning: Could not parse verse part '{verse_part}'. Error: {e}")
        return set()
    return verses

def parse_citation(citation_str: str) -> Optional[Tuple[str, str, Set[int]]]:
    """
    Parses a full citation string (e.g., "Luke 2:16-21") into
    (book_name, chapter_str, verse_set).
    Returns None if parsing fails.
    """
    if not citation_str:
        return None
    
    # Strip any leading/trailing whitespace
    match = CITATION_REGEX.match(citation_str.strip())
    if not match:
        # This is expected for some "readings" like responsorials
        # print(f"Info: Could not parse citation format '{citation_str}'")
        return None
    
    book_name = match.group(1).strip()
    chapter_str = match.group(2) # Keep as string for dict lookup
    verse_part = match.group(3)
    
    verses = parse_verses(verse_part)
    if not verses:
        # print(f"Warning: Failed to parse verses from '{citation_str}'")
        return None # Failed verse parsing
        
    return book_name, chapter_str, verses

def load_ccc_refs(book_name: str, cache: CccRefCache, base_dir: str) -> Optional[Dict[str, Any]]:
    """
    Loads the CCC reference JSON for a given book name.
    Uses a cache to avoid re-loading files.
    Returns the data as a dict, or None if not found/error.
    """
    if book_name in cache:
        return cache[book_name]
    
    # Normalize book name to filename
    # e.g., "1 Corinthians" -> "1-corinthians.json"
    # e.g., "Psalm" -> "psalm.json"
    filename_key = book_name.lower().replace(' ', '-')
    filepath = os.path.join(base_dir, f'{filename_key}.json')
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        cache[book_name] = data
        return data
    except FileNotFoundError:
        # This is common (e.g., for books not referenced in CCC)
        # print(f"Info: No CCC ref file found for '{book_name}' (at {filepath})")
        cache[book_name] = None # Cache failure
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Could not decode JSON for '{book_name}' (at {filepath}). Error: {e}")
        cache[book_name] = None
        return None
    except Exception as e:
        print(f"Error: Unexpected error loading '{filepath}'. Error: {e}")
        cache[book_name] = None
        return None

# --- Main Execution ---

def main():
    """
    Main function to run the coverage analysis.
    """
    print(f"Starting CCC coverage analysis for {START_DATE} to {END_DATE}...")
    print(f"Reading data from: {PROJECT_ROOT}")
    
    ccc_ref_cache: CccRefCache = {}
    all_referenced_ccc_paras: Set[str] = set()
    
    # 1. Load USCCB Readings
    try:
        with open(READINGS_FILE, 'r', encoding='utf-8') as f:
            all_readings = json.load(f)
        if not isinstance(all_readings, list):
             print(f"Error: Readings file {READINGS_FILE} is not a JSON list.")
             return
    except FileNotFoundError:
        print(f"Error: Readings file not found at {READINGS_FILE}")
        print("Please ensure the file exists and the script is in the 'utils' directory.")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {READINGS_FILE}")
        return
        
    print(f"Loaded {len(all_readings)} total readings from {READINGS_FILE}.")

    # 2. Filter readings by date
    filtered_readings = [
        r for r in all_readings 
        if isinstance(r, dict) and r.get('date') and START_DATE <= r['date'] <= END_DATE
    ]
    
    if not filtered_readings:
        print(f"No readings found between {START_DATE} and {END_DATE}.")
        return
        
    print(f"Found {len(filtered_readings)} readings in the date range.")
    
    # 3. Process each reading
    readings_to_check: List[str] = ['reading_1', 'psalm', 'reading_2', 'gospel']
    
    for reading in filtered_readings:
        
        for reading_key in readings_to_check:
            citation_str = reading.get(reading_key)
            
            if not citation_str:
                continue
                
            # 3a. Parse the citation (e.g., "Luke 2:16-21")
            parsed_data = parse_citation(citation_str)
            if not parsed_data:
                continue
                
            book_name, chapter_str, verses = parsed_data
            
            # 3b. Load the CCC ref file for this book (from cache or disk)
            book_refs = load_ccc_refs(book_name, ccc_ref_cache, CCC_REFS_DIR)
            
            if book_refs is None:
                # File not found or error, already warned by loader
                continue
                
            # 3c. Find matching references
            # Check if the chapter string (e.g., "2") is a key in the book's refs
            if chapter_str in book_refs:
                chapter_refs = book_refs[chapter_str]
                if not isinstance(chapter_refs, dict):
                    print(f"Warning: Data for {book_name} Ch. {chapter_str} is not a dict. Skipping.")
                    continue
                    
                for verse_num in verses:
                    verse_str = str(verse_num)
                    # Check if the verse string (e.g., "16") is a key in the chapter's refs
                    if verse_str in chapter_refs:
                        # Found refs! Add them to the global set
                        ccc_paras = chapter_refs[verse_str]
                        if isinstance(ccc_paras, list):
                            all_referenced_ccc_paras.update(ccc_paras)
                        else:
                            print(f"Warning: Ref for {book_name} {chapter_str}:{verse_str} is not a list. Skipping.")
                            
    # 4. Calculate and print results
    print("\n--- Analysis Complete ---")
    
    # Convert string paragraph numbers to integers for categorization
    referenced_para_nums: Set[int] = set()
    for para_str in all_referenced_ccc_paras:
        try:
            referenced_para_nums.add(int(para_str))
        except ValueError:
            print(f"Warning: Non-integer paragraph number '{para_str}' found. Skipping.")
            
    # Categorize paragraphs into sections
    section_1_refs = {p for p in referenced_para_nums if SECTION_1_BOUNDS[0] <= p <= SECTION_1_BOUNDS[1]}
    section_2_refs = {p for p in referenced_para_nums if SECTION_2_BOUNDS[0] <= p <= SECTION_2_BOUNDS[1]}
    section_3_refs = {p for p in referenced_para_nums if SECTION_3_BOUNDS[0] <= p <= SECTION_3_BOUNDS[1]}
    section_4_refs = {p for p in referenced_para_nums if SECTION_4_BOUNDS[0] <= p <= SECTION_4_BOUNDS[1]}
    
    # Calculate totals
    total_unique_refs = len(referenced_para_nums)
    total_percentage = (total_unique_refs / TOTAL_CCC_PARAGRAPHS) * 100
    
    sec1_count = len(section_1_refs)
    sec1_perc = (sec1_count / SECTION_1_TOTAL) * 100
    
    sec2_count = len(section_2_refs)
    sec2_perc = (sec2_count / SECTION_2_TOTAL) * 100
    
    sec3_count = len(section_3_refs)
    sec3_perc = (sec3_count / SECTION_3_TOTAL) * 100
    
    sec4_count = len(section_4_refs)
    sec4_perc = (sec4_count / SECTION_4_TOTAL) * 100
    
    # Print results
    print(f"\n--- Total Coverage ---")
    print(f"Total unique CCC paragraphs referenced: {total_unique_refs}")
    print(f"Total CCC paragraphs in Catechism:   {TOTAL_CCC_PARAGRAPHS}")
    print(f"Overall Coverage: {total_percentage:.2f}%")
    
    print(f"\n--- Coverage by Section ---")
    print(f"Section 1 (1-1065):    {sec1_count:4} / {SECTION_1_TOTAL:4} paragraphs ({sec1_perc:.2f}%)")
    print(f"Section 2 (1066-1690): {sec2_count:4} / {SECTION_2_TOTAL:4} paragraphs ({sec2_perc:.2f}%)")
    print(f"Section 3 (1691-2557): {sec3_count:4} / {SECTION_3_TOTAL:4} paragraphs ({sec3_perc:.2f}%)")
    print(f"Section 4 (2558-2865): {sec4_count:4} / {SECTION_4_TOTAL:4} paragraphs ({sec4_perc:.2f}%)")
    
    # Optional: Uncomment to see all referenced paragraphs
    # print("\nReferenced Paragraphs:")
    # print(sorted(list(all_referenced_ccc_paras), key=int))

if __name__ == "__main__":
    main()