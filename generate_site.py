import os
import xml.etree.ElementTree as ET

# --- CONFIGURATION ---

CATHOLIC_BIBLE_BOOKS = [
    ("Genesis", 50, "Gen", "Genesis"), ("Exodus", 40, "Exod", "Exodus"), ("Leviticus", 27, "Lev", "Leviticus"),
    ("Numbers", 36, "Num", "Numbers"), ("Deuteronomy", 34, "Deut", "Deuteronomy"), ("Joshua", 24, "Josh", "Joshua"),
    ("Judges", 21, "Judg", "Judges"), ("Ruth", 4, "Ruth", "Ruth"), ("1 Samuel", 31, "1Sam", "1 Samuel"),
    ("2 Samuel", 24, "2Sam", "2 Samuel"), ("1 Kings", 22, "1Kgs", "1 Kings"), ("2 Kings", 25, "2Kgs", "2 Kings"),
    ("1 Chronicles", 29, "1Chr", "1 Chronicles"), ("2 Chronicles", 36, "2Chr", "2 Chronicles"), ("Ezra", 10, "Ezra", "Ezra"),
    ("Nehemiah", 13, "Neh", "Nehemiah"), ("Tobit", 14, None, "Tobit"), ("Judith", 16, None, "Judith"),
    ("Esther", 10, "Esth", "Esther"), ("1 Maccabees", 16, None, "1 Maccabees"), ("2 Maccabees", 15, None, "2 Maccabees"),
    ("Job", 42, "Job", "Job"), ("Psalms", 150, "Ps", "Psalms"), ("Proverbs", 31, "Prov", "Proverbs"),
    ("Ecclesiastes", 12, "Eccl", "Ecclesiastes"), ("Song of Songs", 8, "Song", "Song of Solomon"), ("Wisdom", 19, None, "Wisdom"),
    ("Sirach", 51, None, "Sirach"), ("Isaiah", 66, "Isa", "Isaiah"), ("Jeremiah", 52, "Jer", "Jeremiah"),
    ("Lamentations", 5, "Lam", "Lamentations"), ("Baruch", 6, None, "Baruch"), ("Ezekiel", 48, "Ezek", "Ezekiel"),
    ("Daniel", 14, "Dan", "Daniel"), ("Hosea", 14, "Hos", "Hosea"), ("Joel", 3, "Joel", "Joel"),
    ("Amos", 9, "Amos", "Amos"), ("Obadiah", 1, "Obad", "Oba"), ("Jonah", 4, "Jonah", "Jonah"),
    ("Micah", 7, "Mic", "Micah"), ("Nahum", 3, "Nah", "Nahum"), ("Habakkuk", 3, "Hab", "Habakkuk"),
    ("Zephaniah", 3, "Zeph", "Zephaniah"), ("Haggai", 2, "Hag", "Haggai"), ("Zechariah", 14, "Zech", "Zechariah"),
    ("Malachi", 4, "Mal", "Malachi"), ("Matthew", 28, "Matt", "Matthew"), ("Mark", 16, "Mark", "Mark"),
    ("Luke", 24, "Luke", "Luke"), ("John", 21, "John", "John"), ("Acts", 28, "Acts", "Acts"),
    ("Romans", 16, "Rom", "Romans"), ("1 Corinthians", 16, "1Cor", "1 Corinthians"), ("2 Corinthians", 13, "2Cor", "2 Corinthians"),
    ("Galatians", 6, "Gal", "Galatians"), ("Ephesians", 6, "Eph", "Ephesians"), ("Philippians", 4, "Phil", "Philippians"),
    ("Colossians", 4, "Col", "Colossians"), ("1 Thessalonians", 5, "1Thess", "1 Thessalonians"), ("2 Thessalonians", 3, "2Thess", "2 Thessalonians"),
    ("1 Timothy", 6, "1Tim", "1 Timothy"), ("2 Timothy", 4, "2Tim", "2 Timothy"), ("Titus", 3, "Titus", "Titus"),
    ("Philemon", 1, "Phlm", "Philemon"), ("Hebrews", 13, "Heb", "Hebrews"), ("James", 5, "Jas", "James"),
    ("1 Peter", 5, "1Pet", "1 Peter"), ("2 Peter", 3, "2Pet", "2 Peter"), ("1 John", 5, "1John", "1 John"),
    ("2 John", 1, "2John", "2 John"), ("3 John", 1, "3John", "3 John"), ("Jude", 1, "Jude", "Jude"),
    ("Revelation", 22, "Rev", "Revelation")
]

# --- PART 1: XML PARSING ---

def parse_zefania_xml(filepath):
    """Parses Zefania-format XML files (like the DRA)."""
    print(f"Parsing {filepath}...")
    try:
        tree = ET.parse(filepath)
        root = tree.getroot()
        bible_data = {}
        for book in root.findall('BIBLEBOOK'):
            book_id = book.get('bname')
            bible_data[book_id] = {}
            for chapter in book.findall('CHAPTER'):
                chapter_num = int(chapter.get('cnumber'))
                bible_data[book_id][chapter_num] = {}
                for verse in chapter.findall('VERS'):
                    verse_num = int(verse.get('vnumber'))
                    bible_data[book_id][chapter_num][verse_num] = verse.text.strip() if verse.text else ""
        print(f"  -> Parsed {len(bible_data)} books.")
        return bible_data
    except (ET.ParseError, FileNotFoundError) as e:
        print(f"Error with {filepath}: {e}")
        return {}

def parse_osis_xml(filepath):
    """
    Parses OSIS-format XML files (like the KJV) by building the structure
    directly from verse IDs and correctly gathering all associated text.
    """
    print(f"Parsing {filepath}...")
    try:
        # Register the namespace to make searching easier
        ET.register_namespace("osis", "http://www.bibletechnologies.net/2003/OSIS/namespace")
        tree = ET.parse(filepath)
        root = tree.getroot()
        ns = {'osis': 'http://www.bibletechnologies.net/2003/OSIS/namespace'}
        bible_data = {}

        # Iterate through all paragraphs which contain verse text
        for p_tag in root.findall(".//osis:p", ns):
            current_verse_info = None
            # Iterate through all direct children and text nodes of the paragraph
            for item in p_tag.iter():
                # Check if this item is a verse marker
                if item.tag == '{http://www.bibletechnologies.net/2003/OSIS/namespace}verse' and 'osisID' in item.attrib:
                    verse_id = item.get('osisID')
                    parts = verse_id.split('.')
                    if len(parts) == 3:
                        book_id, chapter_str, verse_str = parts
                        try:
                            chapter_num = int(chapter_str)
                            verse_num = int(verse_str)
                            current_verse_info = (book_id, chapter_num, verse_num)

                            # Initialize dictionaries if they don't exist
                            if book_id not in bible_data: bible_data[book_id] = {}
                            if chapter_num not in bible_data[book_id]: bible_data[book_id][chapter_num] = {}
                            if verse_num not in bible_data[book_id][chapter_num]: bible_data[book_id][chapter_num][verse_num] = ""
                        except ValueError:
                            current_verse_info = None
                
                # Append text to the current verse
                if current_verse_info:
                    book_id, chapter_num, verse_num = current_verse_info
                    # Append the text of the current element (e.g., inside <transChange>)
                    if item.text and item.text.strip():
                        bible_data[book_id][chapter_num][verse_num] += " " + item.text.strip()
                    # Append the tail text (text that follows an element)
                    if item.tail and item.tail.strip():
                        bible_data[book_id][chapter_num][verse_num] += " " + item.tail.strip()

        # Clean up leading/trailing spaces from all entries
        for book in bible_data.values():
            for chapter in book.values():
                for verse_num, text in chapter.items():
                    chapter[verse_num] = text.strip()

        print(f"  -> Parsed {len(bible_data)} books from KJV.")
        return bible_data

    except (ET.ParseError, FileNotFoundError) as e:
        print(f"Error with {filepath}: {e}")
        return {}


# --- PART 2: HTML GENERATOR ---
# This function is unchanged but included for completeness.
def create_html_for_chapter(book_name, chapter_num, total_chapters, translations_data, prev_chap, next_chap):
    main_text_html = ""
    sorted_translations = sorted(translations_data.items())
    for i, (trans_abbr, trans_content) in enumerate(sorted_translations):
        active_class = "active" if i == 0 else ""
        main_text_html += f'        <div class="translation-text {trans_abbr.lower()} {active_class}">\n'
        for verse_num, verse_text in sorted(trans_content.items()):
            main_text_html += f'            <p data-verse="{chapter_num}:{verse_num}"><span class="verse-num">{verse_num}</span> {verse_text}</p>\n'
        main_text_html += '        </div>\n'
    book_slug = book_name.lower().replace(" ", "-")
    prev_link = f'<a href="{prev_chap}">← {prev_chap.replace(".html", "").replace("-", " ").title()}</a>' if prev_chap else '<span></span>'
    next_link = f'<a href="{next_chap}">{next_chap.replace(".html", "").replace("-", " ").title()} →</a>' if next_chap else '<span></span>'
    translation_options = ""
    for abbr, _ in sorted_translations:
        translation_options += f'<option value="{abbr.lower()}">{abbr}</option>'
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="The Liturgy Bible visualizes the liturgical use of the biblical text, including the Lectionary for Mass and selections from the Divine Office.">
    <meta name="keywords" content="bible, catholic, liturgy, liturgical, gospel, lectionary, breviary, divine, office, hours, church, {book_name}">
    <title>{book_name} {chapter_num} - Liturgy Bible</title>
    <link rel="stylesheet" href="../style.css">

    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-BGRS7FKZLX"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());

      gtag('config', 'G-BGRS7FKZLX');
    </script>
</head>
<body data-book="{book_slug}" data-chapter="{chapter_num}">
    <header class="top-nav">
        <a href="../index.html"><img src="../images/liturgy-Bible-horiz.png" alt="Liturgy Bible Logo" class="header-logo"></a>
        <div class="header-controls">
            <select id="translation-switcher">
                {translation_options}
            </select>
            <h1 class="header-chapter">{book_name} {chapter_num}</h1>
        </div>
    </header>
    <div class="bible-container">
        <div class="annotations-margin-left"></div>
        <main class="bible-text">
{main_text_html}
        </main>
        <div class="annotations-margin-right"></div>
    </div>
    <hr>
    <footer id="footer" align="center">
        <center>
            <img src="../images/lb.png" width="100px">
            <p class="copyright">&copy; <script>new Date().getFullYear()>document.write(new Date().getFullYear());</script> liturgybible.org</p>
        </center>
    </footer>
    <nav class="bottom-nav">
        {prev_link}
        <span>{book_name} {chapter_num}</span>
        {next_link}
    </nav>
    <script src="../script.js"></script>
</body>
</html>"""
    os.makedirs("bible", exist_ok=True)
    filename = f"bible/{book_slug}-{str(chapter_num).zfill(2)}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_template)


# # --- MAIN EXECUTION (DEBUG MODE) ---
# if __name__ == "__main__":
# #   xml data from open-bibles: https://github.com/seven1m/open-bibles/tree/master
#     kjv_data = parse_osis_xml('xml/eng-kjv.osis.xml')
#     dra_data = parse_zefania_xml('xml/eng-dra.zefania.xml')

#     if not kjv_data or not dra_data:
#         print("\nError: Failed to parse one or both XML files. The data dictionaries are empty.")
#         print("Please ensure your XML files are in an 'xml/' directory and are not corrupted.")
#         exit()

#     print("\n--- Starting DEBUG run for Genesis chapter 1 ---")
    
#     book_name, total_chapters, kjv_id, dra_id = CATHOLIC_BIBLE_BOOKS[0]
#     chapter = 1
    
#     print(f"\n[1] Looking for Book: '{book_name}' with KJV ID: '{kjv_id}' and DRA ID: '{dra_id}'")
    
#     chapter_translations = {}

#     print("\n--- Checking Douay-Rheims (DRA) ---")
#     if dra_id and dra_id in dra_data:
#         print(f"[2a] SUCCESS: Found book ID '{dra_id}' in DRA data.")
#         if chapter in dra_data[dra_id]:
#             print(f"[3a] SUCCESS: Found chapter '{chapter}' in '{dra_id}'.")
#             chapter_translations['DRA'] = dra_data[dra_id][chapter]
#         else:
#             print(f"[3a] FAILURE: Chapter '{chapter}' NOT FOUND in '{dra_id}'. Available chapters: {list(dra_data[dra_id].keys())}")
#     else:
#         print(f"[2a] FAILURE: Book ID '{dra_id}' NOT FOUND in DRA data.")
#         if dra_id: print(f"Available DRA book IDs start with: {list(dra_data.keys())[:5]}...")

#     print("\n--- Checking King James Version (KJV) ---")
#     if kjv_id and kjv_id in kjv_data:
#         print(f"[2b] SUCCESS: Found book ID '{kjv_id}' in KJV data.")
#         if chapter in kjv_data[kjv_id]:
#             print(f"[3b] SUCCESS: Found chapter '{chapter}' in '{kjv_id}'.")
#             chapter_translations['KJV'] = kjv_data[kjv_id][chapter]
#         else:
#             # FIX: Corrected variable from book_id to kjv_id
#             print(f"[3b] FAILURE: Chapter '{chapter}' NOT FOUND in '{kjv_id}'. Available chapters: {list(kjv_data[kjv_id].keys())[:5] if kjv_id in kjv_data else 'BOOK NOT FOUND'}")
#     else:
#         print(f"[2b] FAILURE: Book ID '{kjv_id}' NOT FOUND in KJV data.")
#         if kjv_id: print(f"Available KJV book IDs start with: {list(kjv_data.keys())[:5]}...")

#     print(f"\n[4] Final 'chapter_translations' dictionary has {len(chapter_translations.get('DRA', {}))} DRA verses and {len(chapter_translations.get('KJV', {}))} KJV verses.")
    
#     # --- ENHANCED DEBUGGING: Print sample verses ---
#     if chapter_translations.get('DRA'):
#         print("\n--- Sample verses from DRA ---")
#         for i in range(1, 4):
#             print(f"Verse 1:{i} -> {chapter_translations['DRA'].get(i, 'NOT FOUND')}")

#     if chapter_translations.get('KJV'):
#         print("\n--- Sample verses from KJV ---")
#         for i in range(1, 4):
#             print(f"Verse 1:{i} -> {chapter_translations['KJV'].get(i, 'NOT FOUND')}")
#     # --- END ENHANCED DEBUGGING ---

#     if not chapter_translations or not chapter_translations.get('KJV'):
#         print("\n[5] RESULT: 'chapter_translations' is missing KJV data. Please share this full output.")
#     else:
#         print("\n[5] RESULT: Data found for both translations. The script would normally proceed to generate the HTML file.")
#         print("  - Debug run complete. To generate all files, uncomment the original '__main__' block below and comment out this debug block.")


# --- ORIGINAL MAIN EXECUTION ---
if __name__ == "__main__":
    # xml data from open-bibles: https://github.com/seven1m/open-bibles/tree/master
    kjv_data = parse_osis_xml('xml/eng-kjv.osis.xml')
    dra_data = parse_zefania_xml('xml/eng-dra.zefania.xml')
    if not kjv_data or not dra_data:
        print("\nError: Failed to parse one or both XML files...")
        exit()
    os.makedirs("bible", exist_ok=True)
    print("\n--- Starting HTML file generation ---")
    for i, (book_name, total_chapters, kjv_id, dra_id) in enumerate(CATHOLIC_BIBLE_BOOKS):
        print(f"Processing book: {book_name}")
        book_slug = book_name.lower().replace(" ", "-")
        for chapter in range(1, total_chapters + 1):
            chapter_translations = {}
            if dra_id and dra_id in dra_data and chapter in dra_data[dra_id]:
                chapter_translations['DRA'] = dra_data[dra_id][chapter]
            if kjv_id and kjv_id in kjv_data and chapter in kjv_data[kjv_id]:
                chapter_translations['KJV'] = kjv_data[kjv_id][chapter]
            if not chapter_translations:
                print(f"  - No text found for chapter {chapter}. Skipping.")
                continue
            prev_book_slug = CATHOLIC_BIBLE_BOOKS[i-1][0].lower().replace(" ", "-") if i > 0 else ""
            prev_book_chapters = CATHOLIC_BIBLE_BOOKS[i-1][1] if i > 0 else 0
            next_book_slug = CATHOLIC_BIBLE_BOOKS[i+1][0].lower().replace(" ", "-") if i < len(CATHOLIC_BIBLE_BOOKS)-1 else ""
            prev_chap_name = f"{book_slug}-{str(chapter-1).zfill(2)}.html" if chapter > 1 else f"{prev_book_slug}-{str(prev_book_chapters).zfill(2)}.html" if prev_book_slug else ""
            next_chap_name = f"{book_slug}-{str(chapter+1).zfill(2)}.html" if chapter < total_chapters else f"{next_book_slug}-01.html" if next_book_slug else ""
            create_html_for_chapter(book_name, chapter, total_chapters, chapter_translations, prev_chap_name, next_chap_name)
        print(f"  - Completed {total_chapters} chapters for {book_name}.")
    print("\n✅ All HTML files generated successfully!")




# ```

# ---

# ### Step 3: Update Your JavaScript and CSS

# Your `script.js` needs the new logic to handle the translation switcher, and your `style.css` needs rules to hide the inactive translations.

# #### **Updated `script.js`**
# Add this new function inside the `window.addEventListener('load', ...)` block in your existing `script.js`.

# ```javascript

# # --- MAIN EXECUTION ---
# if __name__ == "__main__":
#     mode = ''
#     while mode not in ['all', 'new']:
#         mode = input("Download mode: Enter 'all' to generate all files, or 'new' to generate only missing files: ").lower().strip()

#     scraped_data = scrape_lectionary_data()
#     os.makedirs("data", exist_ok=True)
#     os.makedirs("bible", exist_ok=True)

#     for i, (book_name, total_chapters) in enumerate(CATHOLIC_BIBLE_BOOKS):
#         print(f"\nProcessing book: {book_name} ({total_chapters} chapters)")
#         book_slug = book_name.lower().replace(" ", "-")
#         book_data = {"lectionaryReadings": scraped_data.get(book_name, {}).get("lectionaryReadings", []), "divineOffice": scraped_data.get(book_name, {}).get("divineOffice", [])}
#         with open(f"data/{book_slug}.json", 'w', encoding='utf-8') as f: json.dump(book_data, f, indent=2)

#         for chapter in range(1, total_chapters + 1):
#             filename = f"bible/{book_slug}-{str(chapter).zfill(2)}.html"
#             if mode == 'new' and os.path.exists(filename):
#                 print(f"  - Chapter {chapter} already exists. Skipping.")
#                 continue
            
#             print(f"  - Generating chapter {chapter}...")
#             verses = get_chapter_text(book_name, chapter)
#             if not verses: continue

#             prev_book_slug = CATHOLIC_BIBLE_BOOKS[i-1][0].lower().replace(" ", "-") if i > 0 else ""
#             prev_book_chapters = CATHOLIC_BIBLE_BOOKS[i-1][1] if i > 0 else 0
#             next_book_slug = CATHOLIC_BIBLE_BOOKS[i+1][0].lower().replace(" ", "-") if i < len(CATHOLIC_BIBLE_BOOKS)-1 else ""
            
#             prev_chap_name = f"{book_slug}-{str(chapter-1).zfill(2)}.html" if chapter > 1 else f"{prev_book_slug}-{str(prev_book_chapters).zfill(2)}.html" if prev_book_slug else ""
#             next_chap_name = f"{book_slug}-{str(chapter+1).zfill(2)}.html" if chapter < total_chapters else f"{next_book_slug}-01.html" if next_book_slug else ""
            
#             create_html_for_chapter(book_name, chapter, verses, prev_chap_name, next_chap_name)

#     print("\n✅ All files generated successfully!")

# window.addEventListener('load', () => {
#     // ... existing code for annotations ...

#     // --- NEW: Translation Switcher Logic ---
#     const switcher = document.getElementById('translation-switcher');
#     if (switcher) {
#         switcher.addEventListener('change', function() {
#             // Hide all translation text divs
#             document.querySelectorAll('.translation-text').forEach(div => {
#                 div.classList.remove('active');
#             });
#             // Show the selected one
#             const selectedTranslation = document.querySelector(`.translation-text.${this.value}`);
#             if (selectedTranslation) {
#                 selectedTranslation.classList.add('active');
#             }
#         });
#     }
# });

# // ... rest of existing code ...
# ```

# #### **Updated `style.css`**
# Add these new rules to your `style.css` file. They will hide the inactive translation text and style the new dropdown.

# ```css
# /* --- New Styles for Translation Switching --- */

# /* Hide all translation containers by default */
# .translation-text {
#     display: none;
# }

# /* Show only the active translation */
# .translation-text.active {
#     display: block;
# }

# /* Styles for the dropdown in the header */
# .header-controls {
#     display: flex;
#     align-items: center;
#     gap: 1rem;
# }

# #translation-switcher {
#     font-family: 'Roboto', sans-serif;
#     font-size: 0.9em;
#     padding: 0.25rem 0.5rem;
#     border-radius: 4px;
#     border: 1px solid #ccc;
#     background-color: #fff;
# }

