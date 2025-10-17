# note: added this because it was difficult to parse KJV poetic sections in the XML

import os
import requests
import time

# --- CONFIGURATION ---

# Define the books and chapters to generate.
# Format: ("Book Name", Total Chapters)
BOOKS_TO_GENERATE = [
    ("Psalms", 150),
    ("Proverbs", 31)
]

# This full list helps in calculating previous/next links accurately.
# The script will only process the books defined in BOOKS_TO_GENERATE.
FULL_BIBLE_BOOK_LIST = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "Ruth", 
    "1 Samuel", "2 Samuel", "1 Kings", "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra", 
    "Nehemiah", "Tobit", "Judith", "Esther", "1 Maccabees", "2 Maccabees", "Job", "Psalms", 
    "Proverbs", "Ecclesiastes", "Song of Songs", "Wisdom", "Sirach", "Isaiah", "Jeremiah", 
    "Lamentations", "Baruch", "Ezekiel", "Daniel", "Hosea", "Joel", "Amos", "Obadiah", "Jonah", 
    "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi", "Matthew", 
    "Mark", "Luke", "John", "Acts", "Romans", "1 Corinthians", "2 Corinthians", "Galatians", 
    "Ephesians", "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians", 
    "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews", "James", "1 Peter", 
    "2 Peter", "1 John", "2 John", "3 John", "Jude", "Revelation"
]

# API-specific names for books if they differ from the canonical name.
API_BOOK_NAMES = {
    "Song of Songs": "Song of Solomon",
    "Psalms": "Psalm" # The bible-api.com uses singular for single chapter requests
}

# --- PART 1: API FETCHER ---

def get_chapter_texts(book_name, chapter_num):
    """
    Fetches a chapter's text for multiple translations from bible-api.com.
    """
    chapter_data = {}
    translations = {
        'KJV': 'kjv',
        'DRA': 'dra'
    }
    api_book_name = API_BOOK_NAMES.get(book_name, book_name).replace(" ", "%20")
    
    for key, api_id in translations.items():
        url = f"https://bible-api.com/{api_book_name}+{chapter_num}?translation={api_id}"
        try:
            response = requests.get(url, timeout=20)
            if response.status_code == 200:
                chapter_data[key] = response.json()['verses']
                print(f"    -> Successfully fetched {key}")
            else:
                print(f"    -> Warning: Status {response.status_code} for {key} from {url}")
                chapter_data[key] = None
        except requests.exceptions.RequestException as e:
            print(f"    -> Error fetching {key}: {e}")
            chapter_data[key] = None
        
        time.sleep(1.5) # Be polite to the API server
        
    return chapter_data

# --- PART 2: HTML GENERATOR ---

def create_html_for_chapter(book_name, chapter_num, total_chapters, translations_data, prev_chap, next_chap):
    """Generates the full HTML file for a single chapter using the provided template."""
    
    book_slug = book_name.lower().replace(" ", "-")

    # Build the HTML for each translation's text
    main_text_html = ""
    # Ensure DRA is first if available, to be the default 'active' class
    sorted_translations = sorted(translations_data.items(), key=lambda x: x[0] != 'DRA')
    
    for i, (trans_abbr, verses) in enumerate(sorted_translations):
        active_class = "active" if i == 0 else ""
        text_html = ""
        if verses:
            # Sort verses by verse number to ensure correct order
            sorted_verses = sorted(verses, key=lambda v: v['verse'])
            for verse in sorted_verses:
                verse_text = verse['text'].strip().replace('\n', ' ')
                text_html += f'            <p data-verse="{chapter_num}:{verse["verse"]}"><span class="verse-num">{verse["verse"]}</span> {verse_text}</p>\n'
        
        main_text_html += f'        <div class="translation-text {trans_abbr.lower()} {active_class}">\n{text_html}        </div>\n'

    # Build the dropdown options
    translation_options = ""
    for abbr, data in sorted_translations:
        if data: # Only add option if data was successfully fetched
            translation_options += f'<option value="{abbr.lower()}">{abbr}</option>'

    # Determine previous/next links
    prev_link = f'<a href="{prev_chap}">← {prev_chap.replace(".html", "").replace("-", " ").title()}</a>' if prev_chap else '<span></span>'
    next_link = f'<a href="{next_chap}">{next_chap.replace(".html", "").replace("-", " ").title()} →</a>' if next_chap else '<span></span>'

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
            <p class="copyright">&copy; <script>document.write(new Date().getFullYear())</script> liturgybible.org</p>
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

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    mode = ''
    while mode not in ['all', 'new']:
        mode = input("Generate 'all' chapters or only 'new' (missing) ones? [all/new]: ").lower().strip()

    os.makedirs("bible", exist_ok=True)
    
    print("\n--- Starting HTML file generation ---")
    
    for book_index, (book_name, total_chapters) in enumerate(BOOKS_TO_GENERATE):
        print(f"Processing book: {book_name}")
        book_slug = book_name.lower().replace(" ", "-")

        for chapter in range(1, total_chapters + 1):
            filename = f"bible/{book_slug}-{str(chapter).zfill(2)}.html"
            if mode == 'new' and os.path.exists(filename):
                print(f"  - Chapter {book_name} {chapter} already exists. Skipping.")
                continue

            print(f"  - Generating {book_name} {chapter}...")
            translations = get_chapter_texts(book_name, chapter)

            if not any(translations.values()):
                print(f"    -> FAILED to get text for chapter {chapter}. Skipping file generation.")
                continue
            
            prev_chap_name, next_chap_name = "", ""
            # Previous link
            if chapter > 1:
                prev_chap_name = f"{book_slug}-{str(chapter-1).zfill(2)}.html"
            elif book_index > 0:
                prev_book_name, prev_book_total_chapters = BOOKS_TO_GENERATE[book_index-1]
                prev_book_slug = prev_book_name.lower().replace(" ", "-")
                prev_chap_name = f"{prev_book_slug}-{str(prev_book_total_chapters).zfill(2)}.html"

            # Next link
            if chapter < total_chapters:
                next_chap_name = f"{book_slug}-{str(chapter+1).zfill(2)}.html"
            elif book_index < len(BOOKS_TO_GENERATE) - 1:
                next_book_name, _ = BOOKS_TO_GENERATE[book_index+1]
                next_book_slug = next_book_name.lower().replace(" ", "-")
                next_chap_name = f"{next_book_slug}-01.html"

            create_html_for_chapter(book_name, chapter, total_chapters, translations, prev_chap_name, next_chap_name)
    
    print("\n✅ All files generated successfully!")

