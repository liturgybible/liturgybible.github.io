import os
from datetime import datetime

# The root URL of your website
BASE_URL = "https://liturgybible.org"

# Relative paths from where the script (utils/sitemap.py) is located
BIBLE_DIR = "../bible"
ROOT_DIR = ".."
SITEMAP_PATH = os.path.join(ROOT_DIR, "sitemap.xml")

FILES_TO_IGNORE = [
    "color_test.html",
    "404.html"
]

# Pages not listed here will get a default priority
PAGE_PRIORITIES = {
    "today.html": "1.0",
    "today-full.html": "1.0",
    "index.html": "0.9",
    "about.html": "0.8"
}
DEFAULT_PRIORITY_BIBLE = "0.7"
DEFAULT_PRIORITY_OTHER = "0.5"


# --- SITEMAP GENERATION ---

def get_html_files(directory):
    """Finds all .html files in a given directory, respecting the ignore list."""
    html_files = []
    for filename in os.listdir(directory):
        if filename.endswith(".html") and filename not in FILES_TO_IGNORE:
            html_files.append(filename)
    return html_files

def generate_sitemap_entry(url_path, last_mod_date, priority):
    """Creates a single <url> entry for the sitemap."""
    # Ensure URLs are relative to the root, e.g., "bible/genesis-01.html"
    url = f"{BASE_URL}/{url_path.replace(os.path.sep, '/')}"
    return f"""
    <url>
        <loc>{url}</loc>
        <lastmod>{last_mod_date}</lastmod>
        <priority>{priority}</priority>
    </url>"""

if __name__ == "__main__":
    print("Starting sitemap generation...")
    
    # Get current date for <lastmod>
    today_iso = datetime.now().strftime('%Y-%m-%d')
    
    sitemap_entries = []
    processed_root_files = set() # Keep track of files we've already added

    # 1. Add high-priority root files first
    print("Processing high-priority root files...")
    for filename, priority in PAGE_PRIORITIES.items():
        if os.path.exists(os.path.join(ROOT_DIR, filename)):
            sitemap_entries.append(generate_sitemap_entry(filename, today_iso, priority))
            processed_root_files.add(filename)
            print(f"  -> Added {filename} with priority {priority}")
        else:
            print(f"  -> Warning: High-priority file not found: {filename}")
            
    # 2. Add other root directory files
    print(f"Scanning rest of root directory: {os.path.abspath(ROOT_DIR)}")
    try:
        root_files = get_html_files(ROOT_DIR)
        other_files_count = 0
        for filename in root_files:
            if filename not in processed_root_files: # Only add if not already processed
                sitemap_entries.append(generate_sitemap_entry(filename, today_iso, DEFAULT_PRIORITY_OTHER))
                processed_root_files.add(filename)
                other_files_count += 1
        print(f"  -> Found {other_files_count} other root files.")
    except FileNotFoundError:
        print(f"  -> Warning: Root directory '{ROOT_DIR}' not found. Skipping root files.")

    # 3. Add bible directory files
    print(f"Scanning bible directory: {os.path.abspath(BIBLE_DIR)}")
    if os.path.isdir(BIBLE_DIR):
        bible_files = get_html_files(BIBLE_DIR) # get_html_files respects ignore list (though none are in /bible/)
        for filename in bible_files:
            # Create a relative path from the root
            relative_path = os.path.join(os.path.basename(BIBLE_DIR), filename)
            sitemap_entries.append(generate_sitemap_entry(relative_path, today_iso, DEFAULT_PRIORITY_BIBLE))
        print(f"  -> Found {len(bible_files)} files in 'bible/'.")
    else:
        print(f"  -> Error: Bible directory '{BIBLE_DIR}' not found. Skipping bible files.")

    # 4. Assemble the full sitemap.xml content
    sitemap_header = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">"""
    
    sitemap_footer = """
</urlset>
"""
    
    full_sitemap = sitemap_header + "".join(sitemap_entries) + sitemap_footer
    
    # 5. Write the sitemap.xml file to the root directory
    try:
        with open(SITEMAP_PATH, 'w', encoding='utf-8') as f:
            f.write(full_sitemap)
        print(f"\n✅ Sitemap successfully generated!")
        print(f"   Total URLs: {len(sitemap_entries)}")
        print(f"   Saved to: {os.path.abspath(SITEMAP_PATH)}")
    except Exception as e:
        print(f"\n❌ Error writing sitemap file: {e}")

