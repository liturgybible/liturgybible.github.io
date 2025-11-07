import json
import os
import re
from collections import defaultdict
from tqdm import tqdm

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
TEXT_INPUT_FILE = os.path.join(SCRIPT_DIR, "ccc-text.json") 
# Output directory will be *one level up* in /data/ccc-refs/
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "..", "data", "ccc-refs")

# --- Bible Book Slug Mapping ---
# Maps various abbreviations to a single canonical slug.
# This is the "brain" of the parser.
BOOK_SLUG_MAP = {
    # Pentateuch
    "gen": "genesis", "genesis": "genesis", "gn": "genesis",
    "ex": "exodus", "exodus": "exodus", "exod": "exodus",
    "lev": "leviticus", "leviticus": "leviticus", "lv": "leviticus",
    "num": "numbers", "numbers": "numbers", "nm": "numbers", "nb": "numbers",
    "deut": "deuteronomy", "deuteronomy": "deuteronomy", "dt": "deuteronomy",
    # Historical
    "josh": "joshua", "joshua": "joshua", "jos": "joshua",
    "judg": "judges", "judges": "judges", "jdg": "judges",
    "ruth": "ruth", "rth": "ruth", "ru": "ruth",
    "1 sam": "1-samuel", "1sam": "1-samuel", "1 samuel": "1-samuel", "1sm": "1-samuel",
    "2 sam": "2-samuel", "2sam": "2-samuel", "2 samuel": "2-samuel", "2sm": "2-samuel",
    "1 kgs": "1-kings", "1kings": "1-kings", "1 kings": "1-kings", "1k": "1-kings",
    "2 kgs": "2-kings", "2kings": "2-kings", "2 kings": "2-kings", "2k": "2-kings",
    "1 chr": "1-chronicles", "1chr": "1-chronicles", "1 chronicles": "1-chronicles", "1ch": "1-chronicles",
    "2 chr": "2-chronicles", "2chr": "2-chronicles", "2 chronicles": "2-chronicles", "2ch": "2-chronicles",
    "ezra": "ezra", "ezr": "ezra",
    "neh": "nehemiah", "nehemiah": "nehemiah", "nh": "nehemiah",
    "tob": "tobit", "tobit": "tobit", "tb": "tobit",
    "jdt": "judith", "judith": "judith", "jth": "judith",
    "esth": "esther", "esther": "esther", "est": "esther",
    "1 macc": "1-maccabees", "1macc": "1-maccabees", "1 maccabees": "1-maccabees", "1mc": "1-maccabees",
    "2 macc": "2-maccabees", "2macc": "2-maccabees", "2 maccabees": "2-maccabees", "2mc": "2-maccabees",
    # Wisdom
    "job": "job", "jb": "job",
    "ps": "psalms", "psalm": "psalms", "psalms": "psalms", "pss": "psalms",
    "prov": "proverbs", "proverbs": "proverbs", "prv": "proverbs", "pr": "proverbs",
    "eccles": "ecclesiastes", "ecclesiastes": "ecclesiastes", "eccl": "ecclesiastes", "qoh": "ecclesiastes", "qo": "ecclesiastes",
    "song": "song-of-songs", "song of songs": "song-of-songs", "sos": "song-of-songs", "cant": "song-of-songs",
    "wis": "wisdom", "wisdom": "wisdom", "ws": "wisdom",
    "sir": "sirach", "sirach": "sirach", "ecclus": "sirach",
    # Prophets
    "isa": "isaiah", "isaiah": "isaiah", "is": "isaiah",
    "jer": "jeremiah", "jeremiah": "jeremiah", "jr": "jeremiah",
    "lam": "lamentations", "lamentations": "lamentations", "la": "lamentations",
    "bar": "baruch", "baruch": "baruch",
    "ezek": "ezekiel", "ezekiel": "ezekiel", "ez": "ezekiel",
    "dan": "daniel", "daniel": "daniel", "dn": "daniel",
    "hos": "hosea", "hosea": "hosea",
    "joel": "joel", "jl": "joel",
    "amos": "amos", "am": "amos",
    "obad": "obadiah", "obadiah": "obadiah", "ob": "obadiah",
    "jonah": "jonah", "jnh": "jonah",
    "mic": "micah", "micah": "micah",
    "nah": "nahum", "nahum": "nahum", "na": "nahum",
    "hab": "habakkuk", "habakkuk": "habakkuk", "hb": "habakkuk",
    "zeph": "zephaniah", "zephaniah": "zephaniah", "zp": "zephaniah",
    "hag": "haggai", "haggai": "haggai", "hg": "haggai",
    "zech": "zechariah", "zechariah": "zechariah", "zc": "zechariah",
    "mal": "malachi", "malachi": "malachi", "ml": "malachi",
    # NT Gospels
    "mt": "matthew", "matthew": "matthew", "matt": "matthew",
    "mk": "mark", "mark": "mark", "mrk": "mark",
    "lk": "luke", "luke": "luke",
    "jn": "john", "john": "john",
    # NT Acts
    "acts": "acts",
    # NT Epistles
    "rom": "romans", "romans": "romans",
    "1 cor": "1-corinthians", "1cor": "1-corinthians", "1 corinthians": "1-corinthians",
    "2 cor": "2-corinthians", "2cor": "2-corinthians", "2 corinthians": "2-corinthians",
    "gal": "galatians", "galatians": "galatians",
    "eph": "ephesians", "ephesians": "ephesians",
    "phil": "philippians", "philippians": "philippians", "php": "philippians",
    "col": "colossians", "colossians": "colossians",
    "1 thes": "1-thessalonians", "1thes": "1-thessalonians", "1 thessalonians": "1-thessalonians",
    "2 thes": "2-thessalonians", "2thes": "2-thessalonians", "2 thessalonians": "2-thessalonians",
    "1 tim": "1-timothy", "1tim": "1-timothy", "1 timothy": "1-timothy", "1tm": "1-timothy",
    "2 tim": "2-timothy", "2tim": "2-timothy", "2 timothy": "2-timothy", "2tm": "2-timothy",
    "titus": "titus", "ti": "titus",
    "philem": "philemon", "philemon": "philemon", "phlm": "philemon",
    "heb": "hebrews", "hebrews": "hebrews",
    "jas": "james", "james": "james", "jm": "james",
    "1 pet": "1-peter", "1pet": "1-peter", "1 peter": "1-peter", "1pt": "1-peter",
    "2 pet": "2-peter", "2pet": "2-peter", "2 peter": "2-peter", "2pt": "2-peter",
    "1 jn": "1-john", "1john": "1-john", "1 john": "1-john",
    "2 jn": "2-john", "2john": "2-john", "2 john": "2-john",
    "3 jn": "3-john", "3john": "3-john", "3 john": "3-john",
    "jude": "jude", "jud": "jude",
    # NT Revelation
    "rev": "revelation", "revelation": "revelation", "rv": "revelation"
}

# --- Regex patterns ---

# Build a dynamic regex pattern to find all book abbreviations
# Sort by length descending to match "1 Cor" before "Cor"
sorted_books = sorted(BOOK_SLUG_MAP.keys(), key=len, reverse=True)
# Join all book keys into a regex pattern, allow space for '1 cor', '1sam'
# Make sure to handle "1" as a separate word, e.g. \b1\s+Cor
book_pattern = r"|".join(
    [re.escape(b).replace(r"\ ", r"\s+") for b in sorted_books]
)
# Pattern to find a book name, followed by chapter/verse
# (e.g., "Gen 1:1-2, 5; 3:15-16")
# This regex is complex:
# 1. (?:^|[\s;(]) - Start of string, whitespace, semicolon, or open parenthesis (non-capturing)
# 2. \s* - Optional whitespace
# 3. (book_pattern) - Capture the book name
# 4. \s+ - At least one space
# 5. ([\d:\s,f.-]+) - Capture the chapter/verse part (e.g., "1:1-2, 5", "3:15-16")
SCRIPTURE_REGEX = re.compile(
    r"(?:^|[\s;(])\s*(" + book_pattern + r")\s+([\d:\s,f.-]*[\d])", 
    re.IGNORECASE
)

# Pattern to clean prefixes/suffixes
CLEAN_REGEX = re.compile(
    r"^(?:Cf\.|cf\.|see|e\.g\.)\s*|(?:\s*\([^)]{0,25}\)\.?\s*)$", 
    re.IGNORECASE
)

def parse_scripture_references(text, para_id):
    """
    Parses a footnote text string and returns a list of individual references.
    
    Example: "Gen 1:1-2, 5; 3:15. Ex 20:1"
    Returns: [
        {"book": "genesis", "ch": 1, "v": 1, "para": "123"},
        {"book": "genesis", "ch": 1, "v": 2, "para": "123"},
        {"book": "genesis", "ch": 1, "v": 5, "para": "123"},
        {"book": "genesis", "ch": 3, "v": 15, "para": "123"},
        {"book": "exodus", "ch": 20, "v": 1, "para": "123"}
    ]
    """
    
    # 1. Clean the string
    # Remove "Cf. " and similar prefixes, and (NABRE) suffixes
    clean_text = CLEAN_REGEX.sub("", text).strip()
    
    # Add a semicolon to the end to help regex find the last match
    clean_text += ";"
    
    # 2. Find all book references
    matches = SCRIPTURE_REGEX.findall(clean_text)
    
    parsed_refs = []

    for book_match, verse_part in matches:
        book_slug = BOOK_SLUG_MAP.get(book_match.lower().strip())
        if not book_slug:
            continue
            
        # Now parse the verse_part, e.g., "1:1-2, 5; 3:15-16"
        # We split by semicolon *within* the verse_part as well
        # (e.g. "Wis 1:13-14; 2:23-24;")
        
        # Split by comma (e.g., 1:1-2, 5)
        # Split by semicolon (e.g., 1:1-2; 3:15)
        
        current_chapter = None
        
        # Split by both comma and semicolon
        parts = re.split(r"[,;]", verse_part)
        
        for part in parts:
            part = part.strip().lower()
            if not part:
                continue
                
            # Remove 'f' or 'ff' (e.g., 1:1f or 1:1ff)
            part = re.sub(r"f+$", "", part)
            
            try:
                # Case 1: Chapter and verse range (e.g., "1:10-15")
                cv_range_match = re.match(r"(\d+):(\d+)-(\d+)", part)
                if cv_range_match:
                    current_chapter = int(cv_range_match.group(1))
                    start_verse = int(cv_range_match.group(2))
                    end_verse = int(cv_range_match.group(3))
                    for v in range(start_verse, end_verse + 1):
                        parsed_refs.append({"book": book_slug, "ch": current_chapter, "v": v, "para": para_id})
                    continue
                    
                # Case 2: Chapter and single verse (e.g., "1:10")
                cv_match = re.match(r"(\d+):(\d+)", part)
                if cv_match:
                    current_chapter = int(cv_match.group(1))
                    verse = int(cv_match.group(2))
                    parsed_refs.append({"book": book_slug, "ch": current_chapter, "v": verse, "para": para_id})
                    continue
                    
                # Case 3: Verse-only range (e.g., "10-15")
                v_range_match = re.match(r"(\d+)-(\d+)", part)
                if v_range_match and current_chapter:
                    start_verse = int(v_range_match.group(1))
                    end_verse = int(v_range_match.group(2))
                    for v in range(start_verse, end_verse + 1):
                        parsed_refs.append({"book": book_slug, "ch": current_chapter, "v": v, "para": para_id})
                    continue
                    
                # Case 4: Single verse (e.g., "10")
                v_match = re.match(r"(\d+)", part)
                if v_match and current_chapter:
                    verse = int(v_match.group(1))
                    parsed_refs.append({"book": book_slug, "ch": current_chapter, "v": verse, "para": para_id})
                    continue
                
                # Case 5: Chapter-only (e.g. "Ps 119")
                # We can't know the verses, so we skip this
                
            except Exception as e:
                # print(f"Warning: Could not parse part '{part}' in '{verse_part}' for {book_match}. Error: {e}")
                pass # Silently fail on parts we can't parse
                
    return parsed_refs

def main():
    print(f"Loading {TEXT_INPUT_FILE}...")
    try:
        with open(TEXT_INPUT_FILE, 'r', encoding='utf-8') as f:
            ccc_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {TEXT_INPUT_FILE} not found.")
        print("Please run the ccc.py scraper first.")
        return
    except json.JSONDecodeError:
        print(f"Error: Failed to decode {TEXT_INPUT_FILE}. Is it corrupted?")
        return

    print("Parsing references from footnotes...")
    
    # Use defaultdict for easier nested dictionary creation
    # master_refs[book_slug][chapter_num][verse_num] = set(para_ids)
    master_refs = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))

    all_refs = []
    
    # Iterate through all paragraphs with a progress bar
    for para_id, data in tqdm(ccc_data.items(), desc="Processing paragraphs"):
        
        # --- MODIFIED ---
        # 1. Parse references from the main paragraph text
        para_text = data.get("text", "")
        if para_text:
            text_refs = parse_scripture_references(para_text, para_id)
            for ref in text_refs:
                master_refs[ref["book"]][str(ref["ch"])][str(ref["v"])].add(ref["para"])

        # 2. Parse references from the footnotes
        footnotes = data.get("footnotes", [])
        for footnote in footnotes:
            fn_text = footnote.get("text", "")
            if fn_text:
                fn_refs = parse_scripture_references(fn_text, para_id)
                # --- END MODIFIED ---
                for ref in fn_refs:
                    # Add paragraph ID to the set for that verse
                    master_refs[ref["book"]][str(ref["ch"])][str(ref["v"])].add(ref["para"])

    print("Reference parsing complete.")
    
    # --- Convert sets to sorted lists and save files ---
    print(f"Saving per-book reference files to {OUTPUT_DIR}...")
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    total_books = 0
    total_refs = 0
    
    # Final structure for JSON
    output_data = {}

    for book_slug, chapters in master_refs.items():
        total_books += 1
        output_data[book_slug] = {}
        for chapter, verses in chapters.items():
            output_data[book_slug][chapter] = {}
            for verse, para_ids_set in verses.items():
                # Convert set to sorted list for stable JSON output
                sorted_para_ids = sorted(list(para_ids_set), key=int)
                output_data[book_slug][chapter][verse] = sorted_para_ids
                total_refs += len(sorted_para_ids)

    # Save each book as its own file
    for book_slug, data in output_data.items():
        file_path = os.path.join(OUTPUT_DIR, f"{book_slug}.json")
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, separators=(',', ':')) # Minified JSON
        except IOError as e:
            print(f"Error writing file {file_path}: {e}")

    print("\n--- Processing Complete ---")
    print(f"Saved {total_books} per-book JSON files.")
    print(f"Found {total_refs} total cross-references.")
    print(f"Output directory: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()


# --- Processing Complete ---
# Saved 59 per-book JSON files.
# Found 6170 total cross-references.