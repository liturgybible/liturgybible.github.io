#!/usr/bin/env python3
"""
Process OR_2-yr.txt to create:
1. OR_2-yr_english.txt - English translation
2. OR_2-yr.csv - CSV with scripture reference and date/usage info
"""

import csv
import re

# Latin to English mappings
LATIN_TO_ENGLISH = {
    # Liturgical seasons
    "TEMPUS ADVENTUS": "Advent",
    "TEMPUS NATIVITATIS": "Christmas",
    "TEMPUS QUADRAGESIMAE 7": "Lent",  # Has footnote marker in original
    "TEMPUS QUADRAGESIMAE": "Lent",
    "TEMPUS PASCHALE": "Easter",
    "TEMPUS PER ANNUM8": "Ordinary Time",  # Has footnote marker in original
    "TEMPUS PER ANNUM": "Ordinary Time",
   "Sacrum Triduum Paschale": "Sacred Paschal Triduum",
    "Hebdomada Sancta": "Holy Week",
    "Sollemnitates Domini": "Solemnities of the Lord",
    
    # Years
    "Anno I": "Year I",
    "Anno II": "Year II",
    
    # Time periods
    "Usque ad diem 16 decembris": "Until December 16",
    "Post diem 16 decembris": "After December 16",
    "Usque ad sollemnitatem Epiphaniae": "Until the Solemnity of the Epiphany",
    "A sollemnitate Epiphaniae": "From the Solemnity of the Epiphany",
    "Usque ad sabbatum hebdomadae V": "Until Saturday of Week V",
    "Post sollemnitatem Ascensionis": "After the Solemnity of the Ascension",
    
    # Days of the week
    "DOM.": "Sunday",
    "fer. 2": "Monday",
    "fer. 3": "Tuesday",
    "fer. 4": "Wednesday",
    "fer. 5": "Thursday",
    "fer. 6": "Friday",
    "sabb.": "Saturday",
    
    # Months/dates
    "dec.": "December",
    "ian.": "January",
    "vel": "or",
    "post": "after",
    "infra oct.": "within the octave of",
    "in oct.": "in the octave of",
    
    # Special days
    "In Nativitate Domini": "On Christmas Day",
    "S. Familiae": "Holy Family",
    "In Epiphania Domini": "On the Epiphany of the Lord",
    "In Baptismate Domini": "On the Baptism of the Lord",
    "Cinerum": "Ash Wednesday",
    "Cin.": "Ash Wednesday",
    "In Palmis de Passione Domini": "Palm Sunday of the Passion of the Lord",
    "In Passione Domini": "On the Passion of the Lord (Good Friday)",
    "sabb. sancto": "Holy Saturday",
    "In Resurrectione Domini": "On the Resurrection of the Lord (Easter Sunday)",
    "DOM. I Paschae": "Easter Sunday",
    "In Ascensione Domini": "On the Ascension of the Lord",
    "DOM. Pentecostes": "Pentecost Sunday",
    "SS.mae Trinitatis": "Most Holy Trinity",
    "SS.mi Corporis et Sanguinis Christi": "Most Holy Body and Blood of Christ (Corpus Christi)",
    "Sacratissimi Cordis Iesu": "Most Sacred Heart of Jesus",
    "Sollemnitas D.N.I.C. universorum Regis": "Solemnity of Our Lord Jesus Christ, King of the Universe",
    "Sollemnitas S. Dei Genetricis Mariae": "Solemnity of Mary, Mother of God",
    
    # Weeks
    "Hebdomada": "Week",
    "Pentecosten": "Pentecost",
    "Pentecostes": "Pentecost",
    "Trinitatem": "Trinity",
    
    # Epiphany rubrics
    "a die 2 ad diem 8 ianuarii occurrente": "",
    "a die 2 ad diem 8 January occurrente": "",
    "In oct. Nat. D.ni": "",
    "In oct. Nat.": "",
    "in oct. Nat.": "",
    "Dom. Epiphaniae": "Epiphany",
    "dom. Epiphaniae": "Epiphany",
    "Paschae": "Easter",
    "SS.mam": "Most Holy",
    "diem": "day",
    "occurrente": "occurring",
    
    # Readings context (for descriptions - partial translations)
    "Vocatio": "The Call of",
    "De": "On/Concerning",
    "Narratio": "The Account of",
    "Visio": "The Vision of",
    "Oratio": "The Prayer of",
    "Laus": "Praise of",
}

# Book abbreviations for Liturgy Bible format (with spaces for multi-word books)
BOOK_ABBREVIATIONS = {
    "Gen": "Gen", "Ex": "Exod", "Lev": "Lev", "Num": "Num", "Deut": "Deut",
    "Ios": "Josh", "Iudic": "Judg", "Rut": "Ru", "1 Sam": "1 Sam", "2 Sam": "2 Sam",
    "1 Reg": "1 Kgs", "2 Reg": "2 Kgs", "1 Chr": "1 Chr", "2 Chr": "2 Chr",
    "Esd": "Ezr", "Neh": "Neh", "Tob": "Tob", "Iudt": "Jdt", "Est": "Est",
    "1 Mac": "1 Macc", "2 Mac": "2 Macc", "Iob": "Job", "Ps": "Ps", "Prov": "Prov",
    "Qoh": "Eccl", "Cant": "Song", "Sap": "Wis", "Sir": "Sir",
    "Is": "Isa", "Ier": "Jer", "Lam": "Lam", "Bar": "Bar", "Ez": "Ezek",
    "Dan": "Dan", "Os": "Hos", "Ioel": "Joel", "Am": "Amos", "Abd": "Ob",
    "Ion": "Jonah", "Mic": "Mic", "Nah": "Nah", "Hab": "Hab", "Soph": "Zeph",
    "Agg": "Hag", "Zac": "Zech", "Mal": "Mal",
    "Mt": "Matt", "Mc": "Mark", "Lc": "Luke", "Io": "John", "Act": "Acts",
    "Rom": "Rom", "1 Cor": "1 Cor", "2 Cor": "2 Cor", "Gal": "Gal", "Eph": "Eph",
    "Phil": "Phil", "Col": "Col", "1 Th": "1 Thess", "2 Th": "2 Thess",
    "1 Tim": "1 Tim", "2 Tim": "2 Tim", "Tit": "Titus", "Phm": "Phlm",
    "Hebr": "Heb", "Iac": "Jas", "1 Petr": "1 Pet", "2 Petr": "2 Pet",
    "1 Io": "1 John", "2 Io": "2 John", "3 Io": "3 John", "Iud": "Jude", "Ap": "Rev"
}

def translate_text(latin_text):
    """Translate Latin text to English using the mapping dictionary."""
    english_text = latin_text
    
    # Sort by length (longest first) to avoid partial replacements
    for latin, english in sorted(LATIN_TO_ENGLISH.items(), key=lambda x: len(x[0]), reverse=True):
        # Use word boundaries for short terms or common prefixes/suffixes to avoid partial matches
        # Escape latin term for regex
        pattern = r'\b' + re.escape(latin) + r'\b'
        # If the term contains non-word characters (like dots), we might need a more flexible boundary or just simple replacement for long phrases
        if len(latin) > 3 and '.' in latin:
             english_text = english_text.replace(latin, english)
        else:
             english_text = re.sub(pattern, english, english_text)
    
    # Clean up double spaces
    english_text = re.sub(r'\s+', ' ', english_text).strip()
    return english_text

def roman_to_arabic(roman):
    """Convert Roman numerals to Arabic numbers."""
    roman_values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100}
    result = 0
    prev_value = 0
    
    for char in reversed(roman):
        value = roman_values.get(char, 0)
        if value < prev_value:
            result -= value
        else:
            result += value
        prev_value = value
    
    return str(result)

def format_scripture_reference(book, chapter_verses):
    """Format scripture reference in Liturgy Bible format."""
    # Map book abbreviation
    book_abbr = BOOK_ABBREVIATIONS.get(book, book)
    
    # Format the verses: replace ", " and "," with ":" for chapter:verse separation
    # First handle the spaced version, then the non-spaced version between digits
    formatted = chapter_verses.replace(", ", ":")
    # Also replace comma without space when between digits (e.g., "9,15" -> "9:15")
    formatted = re.sub(r'(\d),(\d)', r'\1:\2', formatted)
    # Replace semicolons and periods (used for multiple ranges) with commas
    formatted = formatted.replace(";", ",").replace(".", ",")
    # Clean up any double commas or extra spaces
    formatted = re.sub(r',\s*,', ',', formatted)
    formatted = re.sub(r'\s+', ' ', formatted).strip()
    # Ensure consistent spacing after commas
    formatted = re.sub(r',\s*', ', ', formatted)
    
    # Handle multi-chapter citations: fix "chapter:verse - nextchapter:verse" pattern
    # Pattern: "4:14 – 5:7" should become "4:14-5:7"
    # Pattern: "5:1-13, 17b – 6:1" should become "5:1-13, 5:17b-6:1"
    # Pattern: "5:1-2, 5-9, 13-17, 25 – 6:1" should become "5:1-2, 5-9, 13-17, 5:25-6:1"
    def fix_multi_chapter(match):
        ch1 = match.group(1)
        between = match.group(2)  # Could be empty or have verses
        last_verse = match.group(3)  # May include letter suffix like "17b"
        ch2 = match.group(4)
        v2 = match.group(5)  # May include letter suffix
        
        if between:
            # Has intermediate verses: "5:1-2, 5-9, 13-17, 25 – 6:1"
            return f"{ch1}:{between}{ch1}:{last_verse}-{ch2}:{v2}"
        else:
            # No intermediate verses: "4:14 – 5:7"
            return f"{ch1}:{last_verse}-{ch2}:{v2}"
    
    formatted = re.sub(
        r'(\d+):([^:]*?)(\d+[a-z]?)\s*[–-]\s*(\d+):(\d+[a-z]?)',
        fix_multi_chapter,
        formatted
    )
    
    # Handle single-chapter books (Jude, Philemon, Obadiah)
    single_chapter_books = ["Jude", "Phlm", "Ob"]
    if book_abbr in single_chapter_books:
        # If formatted string starts with a number (not "chapter:"), prepend "1:"
        if re.match(r'^\d', formatted):
            formatted = "1:" + formatted
    
    return f"{book_abbr} {formatted}"

def extract_week_or_sunday_number(day_label):
    """Extract Roman numeral from day label (e.g., 'DOM. I' -> 'I', 'Sunday III' -> 'III')."""
    # Look for Roman numerals
    match = re.search(r'\b([IVX]+)\b', day_label)
    if match:
        return match.group(1)
    return None

def extract_scripture_verses(rest_of_line):
    """
    Extract all scripture verses from the rest of the line.
    Pattern: Book followed by chapter/verse info (numbers, commas, periods, dashes, semicolons)
    until we hit a Latin description (capital letter followed by lowercase)
    """
    # Match book name (optional number prefix + letters)
    # Then match all verse-related characters including those after (sic)
    # Verse characters include: digits, spaces, commas, periods, semicolons, dashes, colons, 
    # and special markers like 'a', 'b', '(sic)'
    # Updated to capture verses even after (sic) markers
    match = re.match(r'^(\d\s+)?(\w+)\s+([\d\s,;:.ab–-]+(?:\(sic\)\s*[–-]\s*[\d\s,;:.ab–-]+)*)(?:\s+[A-Z].*)?$', rest_of_line)
    
    if match:
        book_prefix = match.group(1)  # e.g., "1 " or None
        book_name = match.group(2)     # e.g., "Chr" or "Dan"
        verses = match.group(3)         # The full verse specification
        
        # Combine book prefix and name if present
        if book_prefix:
            book = (book_prefix + book_name).strip()
        else:
            book = book_name
        
        # Clean up verses - remove (sic) markers and extra spaces
        verses = verses.replace('(sic)', '').strip()
        verses = re.sub(r'\s+', ' ', verses)
        # Normalize en-dash to regular dash to avoid encoding issues
        verses = verses.replace('–', '-')
        
        return book, verses
    
    return None, None

def process_file():
    """Process the OR_2-yr.txt file."""
    input_file = "/Users/mkudija/Documents/GitHub/liturgybible.github.io/utils/LOTH_2yr_OR/OR_2-yr.txt"
    english_output = "/Users/mkudija/Documents/GitHub/liturgybible.github.io/utils/LOTH_2yr_OR/OR_2-yr_english.txt"
    csv_output = "/Users/mkudija/Documents/GitHub/liturgybible.github.io/utils/LOTH_2yr_OR/OR_2-yr.csv"
    
    english_lines = []
    csv_rows = []
    csv_rows.append(["Scripture Reference", "Liturgical Usage"])
    
    current_season = ""
    current_year = ""
    current_period = ""
    current_week_num = ""  # Track week or Sunday number
    current_special_day = ""  # Track special liturgical days
    last_standard_reading_usage = ""  # Track the last standard reading for alternate/canticle context
    
    skipped_lines = []  # Track lines that might contain readings but weren't parsed
    
    with open(input_file, 'r', encoding='utf-8-sig') as f:
        for line_num, line in enumerate(f, 1):
            line = line.rstrip('\n')
            
            # Track liturgical context
            if line.startswith("TEMPUS") or line.startswith("Sacrum Triduum"):
                current_season = translate_text(line)
                current_period = ""
                current_week_num = ""
                current_special_day = ""
            elif line.startswith("Anno"):
                current_year = translate_text(line)
            elif "Usque ad" in line or "Post diem" in line or "A sollemnitate" in line:
                current_period = translate_text(line)
            elif line.startswith("Hebdomada"):
                current_period = translate_text(line)
                week_match = re.search(r'Hebdomada\s+([IVX]+)', line)
                if week_match:
                    current_week_num = week_match.group(1)
            
            # Translate the line
            english_line = translate_text(line)
            english_lines.append(english_line)
            
            # Parse scripture references for CSV - multiple patterns:
            
            # Pattern 1c: Feast readings with title before scripture (e.g., "I, 34 1 ian. In oct... Mariae Hebr 2, 9-17")
            # Pattern: Year, Num, [Date/Day + Feast title], Scripture ref
            # We capture everything between the number and the book name as the "Title" group
            match_feast = re.match(r'^(I(?:, II)?|II),?\s+(\d+)\s+(.+?)\s+(Hebr|Is|Lam|Ez|Rom|1 Cor|Ex|Ap|Dan|Act|1 Io|1 Mac|2 Mac)\s+(\d.*)', line)
            
            # Pattern 1b: Dated readings (I, number date scripture) - e.g., "I, 21 17 dec."
            match_dated = re.match(r'^(I(?:, II)?|II),?\s+(\d+)\s+(\d+\s+\w+\.)\s+(?!In\s|Sollemnitas)(.+)', line)
            
            # Pattern 1: Standard daily readings (I, number day scripture)
            match_standard = re.match(r'^(I(?:, II)?|II),?\s+(\d+[a-z]?)\s+(DOM\.|fer\. \d|sabb\.|Optional|Alternate)\s+((?:sancto\s+)?(?:In\s+\w+\s+Domini\s+)?)(.+)', line)
            
            # Pattern 2: Alternate readings (Vel: ...)  
            match_alternate = re.match(r'^Vel:.*?:\s*$', line)
            next_line_is_alternate = False
            
            # Pattern 3: Canticle readings (Cant I:|Cant II:|Cant III:)
            match_canticle = re.match(r'^Cant\s+(I{1,3}):\s+(.+)', line)
            
            # Pattern 4: Numbered vigil readings (1.|2.|3.|4.)
            match_numbered = re.match(r'^(\d+)\.\s+(.+)', line)
            
            # Check for false positive feast matches that should be handled by standard or dated logic
            if match_feast:
                title_candidate = match_feast.group(3).strip()
                # Check if it's a standard day (e.g., "DOM. I", "fer. 2")
                if re.match(r'^(DOM\.|fer\.|sabb\.)\s*[IVX\d]*$', title_candidate):
                    match_feast = None
                # Check if it's a dated reading (e.g., "17 dec.")
                elif re.match(r'^\d+\s+\w+\.$', title_candidate):
                    match_feast = None
            
            if match_feast:
                # Feast readings with embedded title
                year_marker = match_feast.group(1)
                entry_num = match_feast.group(2)
                title_full = match_feast.group(3)  # Combined date/day and title
                book_name = match_feast.group(4)
                verses_raw = match_feast.group(5)
                
                # Extract verses properly (handling "2, 1-16 * Text...")
                match_v = re.match(r'^([\d\s,;:.ab–-]+(?:\(sic\)\s*[–-]\s*[\d\s,;:.ab–-]+)*)(?:\s+[A-Z*].*)?$', verses_raw)
                if match_v:
                    verses = match_v.group(1).strip()
                else:
                    verses = verses_raw.split()[0]
                
                # Clean up verses
                verses = verses.replace('(sic)', '').strip()
                verses = re.sub(r'\s+', ' ', verses)
                verses = verses.replace('–', '-')
                
                # Format scripture reference
                scripture_ref = format_scripture_reference(book_name, verses)
                
                # Build usage string
                year_text = f"Year {year_marker}"
                feast_title_english = translate_text(title_full.strip())
                
                # Clean up redundant titles
                feast_title_english = feast_title_english.replace("Wednesday Ash Wednesday", "Ash Wednesday")
                feast_title_english = re.sub(r"Sunday [IVX]+ Palm Sunday", "Palm Sunday", feast_title_english)
                feast_title_english = re.sub(r"Sunday .*?Epiphany", "Epiphany", feast_title_english)
                
                # Fix dates in feast titles (various patterns)
                feast_title_english = feast_title_english.replace("6 January or", "Jan. 6,")
                feast_title_english = feast_title_english.replace("1 January", "Jan. 1,")
                feast_title_english = feast_title_english.replace("25 December", "Dec. 25,")
                feast_title_english = re.sub(r'\b(\d+)\s+Jan\.\s+(or|and)', r'Jan. \1 \2', feast_title_english)
                
                # Remove redundant day descriptions for solemnities
                feast_title_english = re.sub(r'Friday after dom\. [IVX]+ after Pentecost ', '', feast_title_english)
                feast_title_english = re.sub(r'Thursday after Most Holy Trinity ', '', feast_title_english)
                
                # Clean up Epiphany/Baptism rubrics
                feast_title_english = re.sub(r'Sunday after day (\d+) January occurring ', 'Sunday after Jan. \\1, ', feast_title_english)
                feast_title_english = re.sub(r'or Sunday from (\d+) day ad day (\d+) January occurring In Epipha- nia Domini', 'or Sunday from Jan. \\1 to Jan. \\2, Epiphany of the Lord', feast_title_english)
                
                # Final cleanup: remove extra "On" before titles
                feast_title_english = re.sub(r', On the ', ', ', feast_title_english)
                
                # Ensure spacing
                feast_title_english = re.sub(r'\s+', ' ', feast_title_english).strip()
                feast_title_english = feast_title_english.replace(" ,", ",")
                
                year_part = f"Office of Readings, {year_text}:"
                usage = year_part + " " + feast_title_english
                
                last_standard_reading_usage = usage
                csv_rows.append([scripture_ref, usage])
                    
            elif match_dated:
                # Dated readings (e.g., "I, 21 17 dec. Is 40, 1-11")
                year_marker = match_dated.group(1)
                entry_num = match_dated.group(2)
                date_str = match_dated.group(3)  # e.g., "17 dec."
                rest = match_dated.group(4)
                
                # Extract book and verses
                match_ref = re.match(r'^(\d\s+)?(\w+)\s+([\d\s,;:.ab–-]+(?:\(sic\)\s*[–-]\s*[\d\s,;:.ab–-]+)*)(?:\s+[A-Z*].*)?$', rest)
                if match_ref:
                    book_prefix = match_ref.group(1)
                    book_name = match_ref.group(2)
                    verses_raw = match_ref.group(3)
                    
                    if book_prefix:
                        book = (book_prefix + book_name).strip()
                    else:
                        book = book_name
                    
                    # Clean up verses
                    verses = verses_raw.replace('(sic)', '').strip()
                    verses = re.sub(r'\s+', ' ', verses)
                    verses = verses.replace('–', '-')
                    
                    # Format scripture reference
                    scripture_ref = format_scripture_reference(book, verses)
                    
                    # Build usage string with date
                    year_text = f"Year {year_marker}"
                    # Clean and format date (e.g., "17 dec." -> "Dec. 17")
                    date_parts = date_str.split()
                    if len(date_parts) == 2:
                        day_num = date_parts[0]
                        month_abbr = date_parts[1]  # e.g., "dec." or "ian."
                        month_map = {"dec.": "Dec.", "ian.": "Jan."}
                        month_formatted = month_map.get(month_abbr, month_abbr.capitalize())
                        date_formatted = f"{month_formatted} {day_num}"
                    else:
                        date_formatted = translate_text(date_str)
                        # Try to format the leading date part (e.g., "7 Jan. ...")
                        date_formatted = re.sub(r'^(\d+)\s+([A-Za-z.]+)', r'\2 \1', date_formatted)
                    
                    year_part = f"Office of Readings, {year_text}:"
                    usage_parts = []
                    
                    if current_season == "Christmas":
                        usage_parts.append(date_formatted)
                        usage_parts.append(current_season)
                    else:
                        if current_season:
                            usage_parts.append(current_season)
                        usage_parts.append(date_formatted)
                    
                    usage = year_part + " " + ", ".join(usage_parts)
                    last_standard_reading_usage = usage
                    csv_rows.append([scripture_ref, usage])
                    
            elif match_standard:
                year_marker = match_standard.group(1)
                entry_num = match_standard.group(2)
                day = match_standard.group(3)
                special_descriptor = match_standard.group(4).strip()
                rest = match_standard.group(5)
                
                # Check for special day title
                special_day_title = None
                if special_descriptor:
                    # Clean up leading Roman numerals from descriptor
                    clean_descriptor = re.sub(r'^[IVX]+\s+', '', special_descriptor)
                    
                    if "sancto" in special_descriptor:
                        special_day_title = translate_text("sabb. sancto")
                        current_special_day = special_day_title
                    elif ("In" in special_descriptor and "Domini" in special_descriptor) or \
                         "Cinerum" in special_descriptor or "Cin." in special_descriptor or \
                         "Cordis" in special_descriptor or "Corporis" in special_descriptor or \
                         "Trinitatis" in special_descriptor:
                        special_day_title = translate_text(clean_descriptor.strip())
                        current_special_day = special_day_title
                
                # Check if this day has a week/Sunday number
                day_num = extract_week_or_sunday_number(day + " " + rest)
                
                # For Advent/Lent/Easter: if this is a Sunday with a number, update the current week
                if day_num and current_season in ["Advent", "Lent", "Easter"] and day == "DOM.":
                    current_week_num = day_num
                
                # Remove leading Roman numeral if present
                if re.match(r'^[IVX]+\s+', rest):
                    rest = re.sub(r'^[IVX]+\s+', '', rest)
                
                # Extract book and verses
                match_ref = re.match(r'^(\d\s+)?(\w+)\s+([\d\s,;:.ab–-]+(?:\(sic\)\s*[–-]\s*[\d\s,;:.ab–-]+)*)(?:\s+[A-Z*].*)?$', rest)
                if match_ref:
                    book_prefix = match_ref.group(1)
                    book_name = match_ref.group(2)
                    verses_raw = match_ref.group(3)
                    
                    if book_prefix:
                        book = (book_prefix + book_name).strip()
                    else:
                        book = book_name
                    
                    # Clean up verses
                    verses = verses_raw.replace('(sic)', '').strip()
                    verses = re.sub(r'\s+', ' ', verses)
                    verses = verses.replace('–', '-')
                    
                    # Format scripture reference
                    scripture_ref = format_scripture_reference(book, verses)
                    
                    # Build usage string
                    year_text = f"Year {year_marker}"
                    day_text = translate_text(day)
                    
                    # Determine week number
                    week_num_to_add = None
                    if current_week_num and "Week" in current_period:
                        week_num_to_add = roman_to_arabic(current_week_num)
                    elif current_week_num and current_season in ["Advent", "Lent", "Easter"]:
                        week_num_to_add = roman_to_arabic(current_week_num)
                    
                    year_part = f"Office of Readings, {year_text}:"
                    usage_parts = []
                    
                    if special_day_title:
                        # If special day, we might still want the season if it's not redundant
                        # But usually special day title is enough (e.g. "Ash Wednesday")
                        # However, for "Palm Sunday", we might want "Lent, Palm Sunday"? 
                        # User asked for "Year I: Palm Sunday...", so just the title.
                        usage_parts.append(special_day_title)
                    else:
                        if current_season:
                            usage_parts.append(current_season)
                        if week_num_to_add:
                            usage_parts.append(f"Week {week_num_to_add}")
                        if day_num and current_season not in ["Advent", "Lent", "Easter"]:
                            if not week_num_to_add:
                                usage_parts.append(f"{day_text} {roman_to_arabic(day_num)}")
                            else:
                                usage_parts.append(day_text)
                        elif day_num and current_season in ["Advent", "Lent", "Easter"] and day == "DOM.":
                            usage_parts.append("Sunday")
                        else:
                            usage_parts.append(day_text)
                    
                    usage = year_part + " " + ", ".join(usage_parts)
                    last_standard_reading_usage = usage
                    csv_rows.append([scripture_ref, usage])
            elif match_alternate:
                # Next line after "Vel:" contains the alternate reading
                next_line_is_alternate = True
                
            elif match_canticle:
                # Canticle reading (Cant I, II, or III)
                cant_num = match_canticle.group(1)
                rest = match_canticle.group(2)
                
                # Parse scripture reference from canticle
                match_cant_ref = re.match(r'^(\w+)\s+([\d\s,;:.–-]+)(?:\s*:.*)?$', rest)
                if match_cant_ref:
                    book = match_cant_ref.group(1)
                    verses_raw = match_cant_ref.group(2)
                    
                    # Clean verses
                    verses = verses_raw.strip()
                    verses = re.sub(r'\s+', ' ', verses)
                    verses = verses.replace('–', '-')
                    
                    scripture_ref = format_scripture_reference(book, verses)
                    
                    # Use context from current special day or last reading
                    if current_special_day:
                        usage = last_standard_reading_usage.replace("Office of Readings", f"Office of Readings (Canticle {roman_to_arabic(cant_num)})")
                    else:
                        usage = last_standard_reading_usage + f" (Canticle {roman_to_arabic(cant_num)})"
                    
                    csv_rows.append([scripture_ref, usage])
                    
            elif match_numbered:
                # Numbered vigil reading (1., 2., 3., 4.)
                reading_num = match_numbered.group(1)
                rest = match_numbered.group(2)
                
                # Parse scripture reference
                match_num_ref = re.match(r'^(\w+)\s+([\d\s,;:.–-]+)(?:\s*\*.*)?$', rest)
                if match_num_ref:
                    book = match_num_ref.group(1)
                    verses_raw = match_num_ref.group(2)
                    
                    # Clean verses
                    verses = verses_raw.strip()
                    verses = re.sub(r'\s+', ' ', verses)
                    verses = verses.replace('–', '-')
                    
                    scripture_ref = format_scripture_reference(book, verses)
                    
                    # Append Vigil reading number to usage
                    usage = last_standard_reading_usage + f", Vigil Reading {reading_num}"
                    csv_rows.append([scripture_ref, usage])
            
            # Check if we should parse next line as alternate
            elif next_line_is_alternate and line.strip():
                # Parse as alternate reading
                match_alt_ref = re.match(r'^(\w+)\s+([\d\s,;:.–-]+)(?:\s+.*)?$', line)
                if match_alt_ref:
                    book = match_alt_ref.group(1)
                    verses_raw = match_alt_ref.group(2)
                    
                    verses = verses_raw.strip()
                    verses = re.sub(r'\s+', ' ', verses)
                    verses = verses.replace('–', '-')
                    
                    scripture_ref = format_scripture_reference(book, verses)
                    usage = last_standard_reading_usage + ", Alternate"
                    csv_rows.append([scripture_ref, usage])
                next_line_is_alternate = False
            
            # Track potentially skipped lines with scripture references
            elif re.search(r'\b(?:Gen|Ex|Lev|Num|Deut|Is|Ier|Ez|Dan|Os|Mic|Lam|Zac|Hebr|Rom|Mt|Mc|Lc|Io|Act|1 (?:Sam|Reg|Chr|Cor|Mac|Th|Tim|Petr|Io)|2 (?:Sam|Reg|Chr|Cor|Mac|Th|Tim|Petr))\b', line):
                if not any(skip in line for skip in ['lectiones', 'narratio', 'eligere', 'Vigilia', 'interfuerunt']):
                    skipped_lines.append((line_num, line))
    
    # Write English translation
    with open(english_output, 'w', encoding='utf-8') as f:
        f.write('\n'.join(english_lines))
    
    # Write CSV
    with open(csv_output, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(csv_rows)
    
    print(f"✓ Created {english_output}")
    print(f"✓ Created {csv_output}")
    print(f"✓ Processed {len(csv_rows)-1} scripture entries")
    print(f"✓ Expected ~730 entries for 2-year cycle, actual: {len(csv_rows)-1}")
    if skipped_lines:
        print(f"\n⚠ Warning: {len(skipped_lines)} lines with potential scripture references were skipped")
        print("First 10 skipped lines:")
        for line_num, line in skipped_lines[:10]:
            print(f"  Line {line_num}: {line[:80]}...")

if __name__ == "__main__":
    process_file()
