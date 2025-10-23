import os
import re

# --- CONFIGURATION ---
BIBLE_DIR = "../bible/"

def add_verse_ids_to_html(filepath):
    """
    Reads an HTML file line by line, finds paragraphs with data-verse
    and spans with data-verse-part, adds corresponding IDs,
    preserving original formatting. Overwrites the original file.
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        modified_lines = []
        modified = False
        
        # Regex for <p data-verse="chap:verse..."> tags
        p_pattern = re.compile(r'(<p\s+data-verse="(\d+):(\d+)[a-z]*".*?>)', re.IGNORECASE)
        # Regex for <span data-verse-part="chap:versePart"> tags
        span_pattern = re.compile(r'(<span\s+data-verse-part="(\d+):(\d+)([a-z]+)".*?>)', re.IGNORECASE)

        for line in lines:
            new_line = line
            
            # --- Process <p> tags ---
            p_match = p_pattern.search(line)
            if p_match:
                full_tag = p_match.group(1)
                # chapter_num_str = p_match.group(2) # Not used, but captured
                verse_num_str = p_match.group(3)
                
                # Check if the correct id already exists
                id_pattern = f'id="{verse_num_str}"'
                if id_pattern not in full_tag.lower(): # Case-insensitive check
                    # Construct the new tag with the id added
                    id_attribute = f' id="{verse_num_str}"'
                    insert_pos = full_tag.find('data-verse=')
                    if insert_pos != -1:
                         quote_char = full_tag[insert_pos + len('data-verse=')]
                         end_quote_pos = full_tag.find(quote_char, insert_pos + len('data-verse=') + 1)
                         if end_quote_pos != -1:
                              new_tag = full_tag[:end_quote_pos+1] + id_attribute + full_tag[end_quote_pos+1:]
                              new_line = line.replace(full_tag, new_tag)
                              modified = True
                         else:
                              print(f"  -> Warning: P Tag - Could not find closing quote for data-verse in tag: {full_tag} in {os.path.basename(filepath)}")
                    else:
                         print(f"  -> Warning: P Tag - Could not find data-verse attribute start in tag: {full_tag} in {os.path.basename(filepath)}")

            # --- Process <span> tags ---
            # Use the potentially modified line from the <p> tag processing
            span_match = span_pattern.search(new_line)
            if span_match:
                full_tag = span_match.group(1)
                # chapter_num_str = span_match.group(2) # Not used, but captured
                verse_num_str = span_match.group(3)
                part_letter = span_match.group(4)
                span_id_str = f"{verse_num_str}{part_letter}" # e.g., "18a"

                # Check if the correct id already exists
                id_pattern = f'id="{span_id_str}"'
                if id_pattern not in full_tag.lower(): # Case-insensitive check
                     # Construct the new tag with the id added
                    id_attribute = f' id="{span_id_str}"'
                    insert_pos = full_tag.find('data-verse-part=')
                    if insert_pos != -1:
                         quote_char = full_tag[insert_pos + len('data-verse-part=')]
                         end_quote_pos = full_tag.find(quote_char, insert_pos + len('data-verse-part=') + 1)
                         if end_quote_pos != -1:
                              new_tag = full_tag[:end_quote_pos+1] + id_attribute + full_tag[end_quote_pos+1:]
                              # Replace in the potentially already modified line
                              new_line = new_line.replace(full_tag, new_tag)
                              modified = True
                         else:
                              print(f"  -> Warning: Span Tag - Could not find closing quote for data-verse-part in tag: {full_tag} in {os.path.basename(filepath)}")
                    else:
                         print(f"  -> Warning: Span Tag - Could not find data-verse-part attribute start in tag: {full_tag} in {os.path.basename(filepath)}")

            modified_lines.append(new_line)

        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(modified_lines)
            print(f"  -> Added/Updated IDs in {os.path.basename(filepath)}")
        else:
            print(f"  -> No ID changes needed for {os.path.basename(filepath)}")

    except FileNotFoundError:
        print(f"Error: File not found - {filepath}")
    except Exception as e:
        print(f"Error processing {filepath}: {e}")


if __name__ == "__main__":
    print(f"Starting to add verse IDs to HTML files in '{BIBLE_DIR}'...")

    if not os.path.isdir(BIBLE_DIR):
        print(f"Error: Directory '{BIBLE_DIR}' not found. Ensure it exists relative to the script's location.")
        exit()

    file_count = 0
    for filename in os.listdir(BIBLE_DIR):
        if filename.endswith(".html"):
            filepath = os.path.join(BIBLE_DIR, filename)
            print(f"Processing {filename}...")
            add_verse_ids_to_html(filepath)
            file_count += 1

    print(f"\n✅ Process finished. Checked {file_count} HTML files.")

