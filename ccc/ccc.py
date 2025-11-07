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
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "ccc-text.json") 
EXPECTED_PARAGRAPHS = 2865

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

def scrape_page(page_url, header_stack, soup):
    """
    Scrapes a single content page for paragraphs, headers, and footnotes.
    Modifies header_stack in place.
    """
    page_data = {}
    
    # Iterate over all <p> tags recursively
    for el in soup.body.find_all('p'):
        full_text = el.get_text(strip=True)
        if not full_text:
            continue # Skip empty <p> tags

        # --- HEADER LOGIC ---
        # Headers are <p> tags with <b> children
        is_header = False
        if el.b:
            b_text = el.b.get_text(strip=True)
            if (b_text.startswith("PART") or b_text.startswith("SECTION") or
                b_text.startswith("CHAPTER") or b_text.startswith("Article") or
                b_text.startswith("Paragraph") or re.match(r"^[IVXLCDM]+\.", b_text) or
                (b_text.isupper() and len(b_text) > 1 and not re.fullmatch(r"\d+", b_text))):
                
                is_header = True
                header_text = el.get_text(strip=True) # Get all text in header <p>
                
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
        
        if match:
            para_id = match.group(1)
            
            # 3. --- FOOTNOTE LOGIC ---
            para_footnotes = []
            # Find all footnote links (e.g., href="#$Y")
            fn_links = el.find_all('a', href=re.compile(r"#\$[A-Z0-9]+$"))
            
            for link in fn_links:
                fn_ref_name = link['href'][1:] # e.g., $Y
                fn_num = link.get_text(strip=True)
                fn_id = f"fn_{fn_num}"
                
                # Find the corresponding footnote anchor at the bottom
                fn_anchor = soup.find('a', {'name': fn_ref_name})
                
                # --- START: MODIFIED FOOTNOTE PARSING ---
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
                # --- END: MODIFIED FOOTNOTE PARSING ---
                
            # 4. --- TEXT EXTRACTION ---
            # To get *just* the paragraph text, we take the matched text
            # and then strip any footnote text from the end
            
            # Re-get text, but this time extract (remove) footnote tags
            # We must operate on a copy or be careful
            
            # Simpler way: just use the regex-matched text
            # and clean it up.
            
            # Let's clean the *element* and then get the text
            
            # Remove all footnote tags
            for tag in el.find_all(['font', 'sup']):
                tag.extract()
            
            # Get text again, *after* removing footnotes
            clean_text = el.get_text(strip=True)
            
            # Remove the number prefix
            clean_text = re.sub(r"^\d+\s*", "", clean_text)
            
            # Normalize whitespace
            para_text = re.sub(r"\s+", " ", clean_text).strip()
            
            # 5. --- ASSEMBLE DATA ---
            page_data[para_id] = {
                "text": para_text,
                "headers": list(header_stack), # Copy the current stack
                "source_url": page_url,
                "footnotes": para_footnotes
            }

    return page_data

def save_data(data, filepath):
    """Saves the final data dictionary to a JSON file."""
    print(f"Saving data to {filepath}...")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    """Main execution function."""
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


    all_ccc_data = {}
    current_header_stack = []

    try:
        for url in tqdm(content_urls, desc="Scraping pages"):
            try:
                response = requests.get(url)
                response.raise_for_status()
                response.encoding = 'iso-8859-1' # Set encoding
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                page_data = scrape_page(url, current_header_stack, soup)
                all_ccc_data.update(page_data)
                
                time.sleep(0.1) # Be polite to the server
                
            except requests.exceptions.RequestException as e:
                print(f"Warning: Could not scrape {url}. Error: {e}")
                
    except KeyboardInterrupt:
        print("\nScraping interrupted by user.")

    # --- TEST MODE: Print Sample Output ---
    if TEST_MODE:
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
        return # Exit before saving

    # --- Full Run: Final Verification ---
    found_paragraphs = len(all_ccc_data)
    print("\n--- Scraping Complete ---")
    print(f"Total paragraphs found: {found_paragraphs}")
    
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
    print(f"Successfully created {OUTPUT_FILE}.")

if __name__ == "__main__":
    main()