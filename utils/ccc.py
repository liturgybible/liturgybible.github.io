import requests
from bs4 import BeautifulSoup
import json
import os
import re
from urllib.parse import urljoin
import time
from tqdm import tqdm

# --- Constants ---
BASE_URL = "https://www.vatican.va/archive/ENG0015/"
INDEX_PAGE = urljoin(BASE_URL, "_INDEX.HTM")

# Get the directory where the script is located
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
# Save the output file in the same directory as the script
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "../data/ccc-text.json") 
EXPECTED_PARAGRAPHS = 2865

# Set to True to skip scraping and load OUTPUT_FILE to apply text replacements
PARSE_EXISTING_JSON = False

# TEXT REPLACEMENTS ---
# A dictionary of "find": "replace" strings to apply to all paragraph text
# This is applied *after* scraping and *before* saving.
TEXT_REPLACEMENTS = {
    ". the": ". The",
    "? the": "? The",
    "! the": "! The",
    "I Jn": "1 Jn",
    # Add more replacements here...
}

# --- TEST MODE ---
# Set to True to scrape only the first 10 pages and print sample output
# Set to False to run the full scrape
TEST_MODE = False
TEST_PAGES_TO_SCRAPE = 10
TEST_SAMPLES_TO_PRINT = 5
# ---

def get_content_urls(index_url):
    """
    Scrapes the index page to find all content page URLs (e.g., __P1.HTM).
    This page is a simple HTML page with a list of links.
    """
    print(f"Fetching index from {index_url}...")
    try:
        # Fetch the main index page directly
        response = requests.get(index_url)
        response.raise_for_status()
        response.encoding = 'iso-8859-1' # Site uses this encoding
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = set()
        # Find all <a> tags whose href starts with __P and ends with .HTM
        for link in soup.find_all('a', href=re.compile(r"__P.*\.HTM$")):
            full_url = urljoin(index_url, link['href'])
            links.add(full_url)
            
        print(f"Found {len(links)} unique content pages.")
        # Sort links to process them in order
        return sorted(list(links))
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching index page: {e}")
        return []

def process_paragraph_content(el, soup, strip_number=False):
    """
    Extracts text and footnotes from a paragraph element.
    Modifies the element in-place to replace footnote links with asterisks.
    """
    para_footnotes = []
    
    # --- FOOTNOTE LOGIC ---
    # Find all footnote links (e.g., href="#$Y")
    fn_links = el.find_all('a', href=re.compile(r"#\$[A-Z0-9]+$"))
    
    for link in fn_links:
        fn_ref_name = link['href'][1:] # e.g., $Y
        fn_num = link.get_text(strip=True)
        fn_id = f"fn_{fn_num}"
        
        # Find the corresponding footnote anchor at the bottom
        fn_anchor = soup.find('a', {'name': fn_ref_name})
        
        if fn_anchor:
            # The anchor <a> is inside a <b> which is inside a <font>
            # The actual text is in the *next* <font> tag
            text_font_tag = fn_anchor.find_parent('font').find_next_sibling('font')
            
            fn_text = ""
            if text_font_tag:
                fn_text = text_font_tag.get_text(strip=True)
                # Clean up any remaining whitespace
                fn_text = re.sub(r"\s+", " ", fn_text).strip()
            
            para_footnotes.append({"id": fn_id, "text": fn_text})
        
        else:
            # If anchor isn't found, still add, but log it's empty
            para_footnotes.append({"id": fn_id, "text": "[Footnote anchor not found]"})
        
    # --- TEXT EXTRACTION ---
    # Find all footnote links (e.g., href="#$Y")
    fn_links_to_replace = el.find_all('a', href=re.compile(r"#\$[A-Z0-9]+$"))
    
    for link in fn_links_to_replace:
        # The link is inside a <sup> inside a <font>
        # We replace the outer <font> tag with an asterisk
        # NO space after, as the following text node (" As a mother")
        # often already has the leading space.
        font_tag = link.find_parent('font')
        if font_tag:
            font_tag.replace_with("*") # Replace the tag with just an asterisk
        else:
            # Fallback: maybe it's just a <sup>?
            sup_tag = link.find_parent('sup')
            if sup_tag:
                sup_tag.replace_with("*")

    # Preserve <br> tags by replacing them with a text representation
    for br in el.find_all("br"):
        br.replace_with("<br>")

    # Get text again, *after* replacing footnotes
    # We do NOT use strip=True here, as it removes the critical
    # leading space on text nodes that follow a footnote.
    clean_text = el.get_text(strip=False)
    
    # Manually strip leading/trailing whitespace from the whole block
    clean_text = clean_text.strip()
    
    if strip_number:
        # Remove the number prefix (which is now at the start)
        clean_text = re.sub(r"^\d+\s*", "", clean_text)
    
    # Normalize internal whitespace (e.g., newlines, tabs) to a single space
    para_text = re.sub(r"\s+", " ", clean_text).strip()
    
    return para_text, para_footnotes

def scrape_page(page_url, soup):
    """
    Scrapes a single content page for paragraphs, headers, and footnotes.
    """
    page_data = {}
    
    # --- HEADERS ---
    # 1. Get the base header stack from the <meta name="part"> tag.
    # This is more reliable than passing a stack between page loads.
    meta_tag = soup.find('meta', {'name': 'part'})
    header_stack = [] 
    if meta_tag and meta_tag.get('content'):
        content_str = meta_tag.get('content')
        # Split by ' > ' and strip whitespace from each header
        header_stack = [h.strip() for h in content_str.split(' > ')]
    
    current_para_id = None

    # Iterate over all <p> tags recursively
    for el in soup.body.find_all('p'):
        full_text = el.get_text(strip=True)
        if not full_text:
            continue # Skip empty <p> tags

        # --- HEADER LOGIC ---
        # Headers are <p> tags with <b> children.
        # These headers (like "IN BRIEF" or "I.") modify the stack
        # for the content *below* them on the *same page*.
        is_header = False
        if el.b:
            b_text = el.b.get_text(separator=" ", strip=True)
            b_text = re.sub(r'\s+', ' ', b_text).strip()
            
            if (b_text.startswith("PART") or b_text.startswith("SECTION") or
                b_text.startswith("CHAPTER") or b_text.startswith("Article") or
                b_text.startswith("Paragraph") or re.match(r"^[IVXLCDM]+\.", b_text) or
                (b_text.isupper() and len(b_text) > 1 and not re.fullmatch(r"\d+", b_text))):
                
                is_header = True
                header_text = el.get_text(separator=" ", strip=True)
                header_text = re.sub(r'\s+', ' ', header_text).strip()
                
                # Reset current_para_id on header to prevent appending across sections
                current_para_id = None

                # Apply the stack-slicing logic to the *current* page's stack
                if header_text.startswith("PART"):
                    header_stack[:] = [header_text]
                elif header_text.startswith("SECTION"):
                    header_stack[1:] = [header_text]
                elif header_text.startswith("CHAPTER"):
                    header_stack[2:] = [header_text]
                elif header_text.startswith("Article"):
                    header_stack[3:] = [header_text]
                elif header_text.startswith("Paragraph"):
                    header_stack[4:] = [header_text]
                elif re.match(r"^[IVXLCDM]+\.", header_text) or (header_text.isupper() and not re.fullmatch(r"\d+", header_text)):
                    header_stack[5:] = [header_text]
        
        if is_header:
            continue # This element was a header, skip to next <p>

        # --- PARAGRAPH LOGIC ---
        # Check if the plain text of the <p> tag starts with a number
        match = re.match(r"^(\d+)\s+(.*)", full_text, re.DOTALL)
        
        # Check for indentation (quoted section)
        is_indented = False
        if el.get('style') and 'margin-left' in el.get('style'):
            is_indented = True

        if match:
            para_id = match.group(1)
            current_para_id = para_id
            
            para_text, para_footnotes = process_paragraph_content(el, soup, strip_number=True)
            
            # 5. --- ASSEMBLE DATA ---
            page_data[para_id] = {
                "text": para_text,
                # FIX: Remove duplicates from header list while preserving order
                "headers": list(dict.fromkeys(header_stack).keys()), # Copy + Dedupe
                "source_url": page_url,
                "footnotes": para_footnotes
            }
        
        elif current_para_id and is_indented:
            # Continuation paragraph (quoted text) - MUST be indented
            # Append to the current paragraph
            para_text, para_footnotes = process_paragraph_content(el, soup, strip_number=False)
            
            if para_text:
                page_data[current_para_id]["text"] += "<br>" + para_text
            
            if para_footnotes:
                page_data[current_para_id]["footnotes"].extend(para_footnotes)
        
        else:
            # Not a numbered paragraph and NOT indented -> Treat as HEADER
            # This catches headers that are not bolded or otherwise missed by the initial check
            header_text = el.get_text(separator=" ", strip=True)
            header_text = re.sub(r'\s+', ' ', header_text).strip()
            
            # Reset current_para_id on header to prevent appending across sections
            current_para_id = None

            # Apply the stack-slicing logic to the *current* page's stack
            if header_text.startswith("PART"):
                header_stack[:] = [header_text]
            elif header_text.startswith("SECTION"):
                header_stack[1:] = [header_text]
            elif header_text.startswith("CHAPTER"):
                header_stack[2:] = [header_text]
            elif header_text.startswith("Article"):
                header_stack[3:] = [header_text]
            elif header_text.startswith("Paragraph"):
                header_stack[4:] = [header_text]
            elif re.match(r"^[IVXLCDM]+\.", header_text) or (header_text.isupper() and not re.fullmatch(r"\d+", header_text)):
                header_stack[5:] = [header_text]

    return page_data

def save_data(data, filepath):
    """Saves the final data dictionary to a JSON file."""
    print(f"Saving data to {filepath}...")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    """Main execution function."""
    
    all_ccc_data = {}

    if PARSE_EXISTING_JSON:
        print(f"--- PARSE EXISTING JSON MODE ---")
        print(f"Loading data from {OUTPUT_FILE}...")
        if not os.path.exists(OUTPUT_FILE):
            print(f"Error: File not found: {OUTPUT_FILE}")
            print("Cannot re-parse. Set PARSE_EXISTING_JSON = False to scrape.")
            return
        
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            all_ccc_data = json.load(f)
        print(f"Loaded {len(all_ccc_data)} paragraphs from file.")
        
    else:
        print("Starting CCC Scraper...")
        content_urls = get_content_urls(INDEX_PAGE)
        
        if not content_urls:
            print("No content URLs found. Exiting.")
            return

        if TEST_MODE:
            print(f"\n--- !!! TEST MODE ACTIVE !!! ---")
            print(f"Will scrape a maximum of {TEST_PAGES_TO_SCRAPE} pages.")
            content_urls = content_urls[0:TEST_PAGES_TO_SCRAPE]
            print(f"--- !!! ---------------------- !!!\n")

        try:
            for url in tqdm(content_urls, desc="Scraping pages"):
                try:
                    response = requests.get(url)
                    response.raise_for_status()
                    response.encoding = 'iso-8859-1' # Set encoding
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    page_data = scrape_page(url, soup)
                    all_ccc_data.update(page_data)
                    
                    time.sleep(0.1) # Be polite to the server
                    
                except requests.exceptions.RequestException as e:
                    print(f"Warning: Could not scrape {url}. Error: {e}")
                    
        except KeyboardInterrupt:
            print("\nScraping interrupted by user.")

    # --- TEST MODE: Print Sample Output (if not re-parsing) ---
    if TEST_MODE and not PARSE_EXISTING_JSON:
        print("\n\n--- TEST MODE: SAMPLE OUTPUT ---")
        if not all_ccc_data:
            print("No paragraphs found. The parsing logic may still be incorrect.")
        else:
            # Sort by paragraph ID
            sorted_items = sorted(all_ccc_data.items(), key=lambda item: int(item[0]))
            
            for i, (para_id, data) in enumerate(sorted_items):
                if i >= TEST_SAMPLES_TO_PRINT:
                    break
                print("\n==============================")
                print(f"PARAGRAPH: {para_id}")
                print(f"  SOURCE: {data['source_url']}")
                print(f"  HEADERS: {data['headers']}")
                print(f"  TEXT: {data['text'][:120]}...")
                print(f"  FOOTNOTES: {data['footnotes']}")
                print("==============================")
        print(f"\nTest mode finished. Found {len(all_ccc_data)} paragraphs.")
        print("Data was NOT saved.")
        return # Exit before saving or replacements

    # --- NEW: APPLY TEXT REPLACEMENTS ---
    if TEXT_REPLACEMENTS:
        print(f"\nApplying {len(TEXT_REPLACEMENTS)} text replacement(s)...")
        for para_id in tqdm(all_ccc_data.keys(), desc="Applying replacements"):
            original_text = all_ccc_data[para_id]['text']
            modified_text = original_text
            for find_str, replace_str in TEXT_REPLACEMENTS.items():
                modified_text = modified_text.replace(find_str, replace_str)
            
            all_ccc_data[para_id]['text'] = modified_text
    else:
        print("\nNo text replacements defined. Skipping.")


    # --- Full Run: Final Verification ---
    found_paragraphs = len(all_ccc_data)
    print("\n--- Processing Complete ---")
    print(f"Total paragraphs processed: {found_paragraphs}")
    
    if not PARSE_EXISTING_JSON: # Only run verification if we did a fresh scrape
        if found_paragraphs == EXPECTED_PARAGRAPHS:
            print(f"Success! Found all {EXPECTED_PARAGRAPHS} paragraphs.")
        else:
            print(f"Warning: Expected {EXPECTED_PARAGRAPHS} paragraphs, but found {found_paragraphs}.")
            # Check for missing paragraphs
            expected_set = set(range(1, EXPECTED_PARAGRAPHS + 1))
            found_set = set(int(k) for k in all_ccc_data.keys())
            missing = sorted(list(expected_set - found_set))
            if missing:
                print(f"Missing paragraphs: {missing[:20]}..." if len(missing) > 20 else f"Missing paragraphs: {missing}")

    # Save the file
    save_data(all_ccc_data, OUTPUT_FILE)
    if PARSE_EXISTING_JSON:
        print(f"Successfully re-processed and saved {OUTPUT_FILE}.")
    else:
        print(f"Successfully created {OUTPUT_FILE}.")

if __name__ == "__main__":
    main()