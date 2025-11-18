#!/usr/bin/env python3

"""
This script scrapes the Order of Mass from liturgies.net to create
a JSON file for use on liturgybible.org.
"""

import requests
import re
import json
import os
from bs4 import BeautifulSoup

# The URL to scrape (for reference)
SOURCE_URL = "https://www.liturgies.net/Liturgies/Catholic/roman_missal/roman_missal_order_of_mass.htm"

# The output directory and file
OUTPUT_DIR = "../data"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "roman-missal-text.json")

def clean_content_html(html_fragment):
    """
    Cleans a raw HTML fragment scraped from the site.
    """
    # Convert red text (rubrics) to <span class="rubric">
    html = re.sub(
        r'<font color="#ff0000">(.*?)</font>',
        r'<span class="rubric">\1</span>',
        html_fragment,
        flags=re.DOTALL | re.IGNORECASE
    )
    
    # Remove black text <font> tags, keeping only the content
    html = re.sub(
        r'<font color="#000000">(.*?)</font>',
        r'\1',
        html,
        flags=re.DOTALL | re.IGNORECASE
    )
    
    # Remove other font tags (like #003265)
    html = re.sub(
        r'<font color="#003265">(.*?)</font>',
        r'\1',
        html,
        flags=re.DOTALL | re.IGNORECASE
    )
    
    # Remove any other stray font tags
    html = re.sub(r'</?font[^>]*>', '', html, flags=re.IGNORECASE)
    
    # Clean up weird Wingdings fonts
    html = re.sub(r'<font face="Wingdings".*?>.*?</font>', '&#10013;', html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r'<font face="Times New Roman".*?>', '', html, flags=re.IGNORECASE | re.DOTALL)


    # Convert separator lines to <hr>
    html = re.sub(
        r'____________________________________________________________',
        '<hr>',
        html
    )
    # Shorter HR
    html = re.sub(
        r'____________________',
        '<hr class="short">',
        html
    )
    
    # Strip whitespace and <br> tags from the beginning and end
    # Also strip stray <b> </b> tags that are often empty
    html_cleaned = html.strip(' \n\t<br><b></b><b> </b>')
    # Fix for empty <font> tags that become empty <span>
    html_cleaned = re.sub(r'<span class="rubric">\s*</span>', '', html_cleaned, flags=re.IGNORECASE)
    
    return html_cleaned.strip(' \n\t<br>')


def parse_order_of_mass():
    """
    Fetches and parses the Order of Mass.
    """
    print(f"Fetching data from {SOURCE_URL}...")
    try:
        response = requests.get(SOURCE_URL)
        response.raise_for_status()
        html_content = response.text
    except requests.RequestException as e:
        print(f"Error: Could not fetch URL: {e}")
        return

    print("Parsing HTML content...")
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find the header text first
    header_tag = soup.find('b', string=re.compile(r'\s*THE ORDER OF MASS\s*'))
    
    if not header_tag:
        print("Error: Could not find the header 'THE ORDER OF MASS' on the page.")
        return

    # Find the <body> tag directly, as parent lookup is unreliable
    content_area = soup.find('body')
    
    if not content_area:
        print("Error: Could not find its parent 'body' container. Scraping failed.")
        return
    else:
        print("Found parent 'body' container.")

    # Get the raw HTML string of the content area
    # --- THIS IS THE FIX ---
    # Instead of using str(content_area), which is parsed by BeautifulSoup,
    # use the raw html_content from requests. This prevents BS4 from
    # "fixing" the HTML in a way that breaks our regex.
    td_html = html_content
    
    # --- THIS IS THE CORRECTED REGEX ---
    # This regex finds the number, a period, an optional space, and the closing </font>
    # tag, ONLY if it is immediately followed by a red font tag.
    
    # Pattern:
    # (\d+)           # Group 1: The number (e.g., "139" or "23")
    # \. ?</font>     # Literal ".</font>" or ". </font>" (optional space)
    # (?=<font color="#ff0000">) # A positive lookahead: must be *followed by* a red font tag
    
    para_starts = list(re.finditer(
        r'(\d+)\. ?</font>(?=<font color="#ff0000">)',
        td_html,
        flags=re.IGNORECASE | re.DOTALL
    ))
    
    # --- END NEW UPDATED REGEX ---
    
    if not para_starts:
        print("Error: Could not find any paragraph markers. The regex may be wrong.")
        return

    all_data = {}
    running_headers = []

    print(f"Found {len(para_starts)} paragraphs. Processing...")

    for i, match in enumerate(para_starts):
        number = match.group(1)
        
        # 1. Find Headers for this section
        start_of_header_search = para_starts[i-1].end() if i > 0 else 0
        end_of_header_search = match.start()
        
        header_slice = td_html[start_of_header_search:end_of_header_search]
        header_soup = BeautifulSoup(header_slice, 'html.parser')
        
        found_headers = [
            h.get_text(strip=True) 
            for h in header_soup.find_all('b') 
            if h.get_text(strip=True) and h.get_text(strip=True).strip()
        ]
        
        if found_headers:
            filtered_headers = [h for h in found_headers if h]
            if not filtered_headers:
                continue

            # This logic updates the running list of headers
            # It's not perfect, but it's based on the site's structure
            if filtered_headers[0].isupper():
                # If the new header is all caps, it's a "major" header
                try:
                    # Check if it's already in the list (e.g., "THE LITURGY OF THE WORD")
                    idx = running_headers.index(filtered_headers[0])
                    # If so, reset the list to that point
                    running_headers = running_headers[:idx]
                except ValueError:
                    # If it's a *new* all-caps header, reset the list
                    if len(filtered_headers[0]) > 5: # simple check to avoid short "OR:"
                         running_headers = []
                
                running_headers.extend(filtered_headers)
            
            else:
                # If it's not all caps, it's a "minor" header
                # Pop the last minor header to replace it
                if running_headers and not running_headers[-1].isupper():
                    running_headers.pop()
                running_headers.extend(filtered_headers)
            
            # De-duplicate
            seen = set()
            running_headers = [h for h in running_headers if not (h in seen or seen.add(h))]

        
        # 2. Get Content for this section
        # Content is from the *end* of *this* marker to the
        # *start* of the *next* marker (or end of string).
        
        start_pos = match.end() 
        end_pos = para_starts[i+1].start() if i + 1 < len(para_starts) else len(td_html)
        
        content_html = td_html[start_pos:end_pos]

        # 2.5: Before cleaning, check if this slice contains the footer
        if "StatCounter Code" in content_html or "Liturgy Archive" in content_html:
            print(f"Stopping before paragraph {number}, found footer content.")
            break # Stop processing, we've hit the footer
        
        # 3. Clean and Store Data
        cleaned_html = clean_content_html(content_html)
        
        # Don't save empty paragraphs
        if not cleaned_html:
            print(f"Skipping paragraph {number}, content is empty after cleaning.")
            continue
            
        all_data[number] = {
            "text": cleaned_html,
            "headers": list(running_headers), # Store a *copy*
            "source_url": SOURCE_URL
        }

    # 4. Write to file
    print(f"Writing data for {len(all_data)} paragraphs to {OUTPUT_FILE}...")
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
            
        print("Done.")
        print(f"Successfully created {OUTPUT_FILE}")
        
    except IOError as e:
        print(f"Error: Could not write file: {e}")

if __name__ == "__main__":
    parse_order_of_mass()