#!/usr/bin/env python3
"""
Preprocess OR_2-yr.txt to normalize formatting for parsing.

This script combines split lines for feasts, solemnities, and special readings
into single lines that can be easily parsed by process_or_2yr.py.
It also adds metadata prefixes to standalone alternate readings.

This combines the logic of the previous fix_feasts.py and fix_all.py scripts.
"""

def preprocess_file():
    input_file = "/Users/mkudija/Documents/GitHub/liturgybible.github.io/utils/LOTH_2yr_OR/OR_2-yr.txt"
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"Read {len(lines)} lines from {input_file}")
    
    # --- PHASE 1: Fix initial feast readings (originally from fix_feasts.py) ---
    # These line numbers refer to the ORIGINAL file state
    combine_ranges_1 = [
        (85, 87, "Year I: Mary Mother of God"),
        (103, 106, "Year I: Epiphany"),
        (125, 127, "Year I: Baptism of the Lord"),
        (139, 140, "Year II: Mary Mother of God"),
        (156, 158, "Year II: Epiphany"),
        (177, 179, "Year II: Baptism of the Lord"),
    ]
    
    # Sort in reverse order to process from bottom up to preserve indices
    combine_ranges_1.sort(reverse=True)
    
    for first_idx_1, last_idx_1, desc in combine_ranges_1:
        first_idx = first_idx_1 - 1
        last_idx = last_idx_1 - 1
        
        if first_idx < len(lines) and last_idx < len(lines):
            combined = ''.join(lines[first_idx:last_idx+1]).replace('\n', ' ').strip() + '\n'
            lines[first_idx] = combined
            for i in range(first_idx + 1, last_idx + 1):
                if i < len(lines):
                    del lines[first_idx + 1]
            print(f"✓ Phase 1: Combined lines {first_idx_1}-{last_idx_1}: {desc}")

    # --- PHASE 2: Fix remaining edge cases (originally from fix_all.py) ---
    # These line numbers refer to the file state AFTER Phase 1
    combine_ranges_2 = [
        (230, 232, "Year I: Palm Sunday"),
        (336, 338, "Year II: Palm Sunday"),
        (241, 242, "Year I: Good Friday optional Lam 2"),
        (348, 349, "Year II: Good Friday optional Jer 15"),
        (448, 450, "Year I: Pentecost"),
        (552, 554, "Year II: Pentecost"),
        (557, 558, "Years I & II: Most Holy Trinity"),
        (559, 562, "Years I & II: Corpus Christi"),
        (563, 564, "Years I & II: Sacred Heart"),
        (952, 954, "Year I: Christ the King"),
        (1329, 1330, "Year II: Christ the King"),
    ]
    
    combine_ranges_2.sort(reverse=True)
    
    for first_idx_1, last_idx_1, desc in combine_ranges_2:
        first_idx = first_idx_1 - 1
        last_idx = last_idx_1 - 1
        
        if first_idx < len(lines) and last_idx < len(lines):
            combined = ''.join(lines[first_idx:last_idx+1]).replace('\n', ' ').strip() + '\n'
            lines[first_idx] = combined
            for i in range(first_idx + 1, last_idx + 1):
                if i < len(lines):
                    del lines[first_idx + 1]
            print(f"✓ Phase 2: Combined lines {first_idx_1}-{last_idx_1}: {desc}")
            
    # --- PHASE 3: Normalize standalone alternate readings ---
    for i, line in enumerate(lines):
        line_text = line.strip()
        
        # Lam 2, 10-22 - Good Friday Yr I optional
        if line_text.startswith("Lam 2, 10-22"):
            lines[i] = "I, 92a Optional Lam 2, 10-22 Miserabilis conditio civitatis et imploratio\n"
            print(f"✓ Phase 3: Fixed line {i+1}: Year I Good Friday optional Lam 2")
        
        # Lam 3, 1-33 - Good Friday Yr I alternate
        elif line_text.startswith("Lam 3, 1-33 Planctus"):
            lines[i] = "I, 93a Alternate Lam 3, 1-33 Planctus et spes\n"
            print(f"✓ Phase 3: Fixed line {i+1}: Year I Good Friday alternate Lam 3")
        
        # Lam 5, 1-22 - Holy Saturday Yr I alternate
        elif line_text.startswith("Lam 5, 1-22 Oratio"):
            lines[i] = "I, 94a Alternate Lam 5, 1-22 Oratio Ieremiae prophetae\n"
            print(f"✓ Phase 3: Fixed line {i+1}: Year I Holy Saturday alternate Lam 5")
        
        # Jer 15, 10-21 - Good Friday Yr II optional (combined but needs prefix if standalone)
        elif line_text.startswith("Ier 15, 10-21"):
            lines[i] = "II, 92a Optional Ier 15, 10-21 Lamentatio prophetae. vocatio eius iteratur\n"
            print(f"✓ Phase 3: Fixed line {i+1}: Year II Good Friday optional Jer 15")
        
        # Jer 16, 1-15 - Good Friday Yr II alternate
        elif line_text.startswith("Ier 16, 1-15 Solitudo"):
            lines[i] = "II, 93a Alternate Ier 16, 1-15 Solitudo prophetae\n"
            print(f"✓ Phase 3: Fixed line {i+1}: Year II Good Friday alternate Jer 16")
        
        # Jer 20, 7-18 - Holy Saturday Yr II alternate
        elif line_text.startswith("Ier 20, 7-18 Anxietates"):
            lines[i] = "II, 94a Alternate Ier 20, 7-18 Anxietates prophetae\n"
            print(f"✓ Phase 3: Fixed line {i+1}: Year II Holy Saturday alternate Jer 20")
        
        # Fix typo: II,371 -> II, 371
        elif "II,371" in line_text:
            lines[i] = line.replace("II,371", "II, 371")
            print(f"✓ Phase 3: Fixed line {i+1}: Added missing space in II,371")

    # Write back
    with open(input_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"\n✓ Preprocessing complete. File updated: {input_file}")

if __name__ == "__main__":
    preprocess_file()
