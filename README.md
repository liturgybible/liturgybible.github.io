# liturgybible.org



## Biblical Text

1. `generate_site_xml.py` parses the files in `xml/` to build HTML files for every chapter of the Bible. This is the preferred method.

2. XML parsing fails for certain chapters in the KJV XML due to verse formatting. For problematic chapters, they can be build using `generate_site_api.py`, which generates HTML files using an API.



## Liturgical Annotations

1. Data is sourced, cleaned, and formatted in [Liturgy Bible Data - Google Sheets](https://docs.google.com/spreadsheets/d/1GB48rM6wN8Ghrj4Hfggb8WEqDi64d9VOiZO0uTUddRs/edit?gid=1148348297#gid=1148348297).

2. Copy/paste the `Data Export` tab to `liturgy_bible_data.csv`

3. Run `liturgy_bible_data.py`, which parses `liturgy_bible_data.csv` and generates a JSON data file for each chapter of the Bible in `data/`


## Test Site

```bash
python3 -m http.server
http://localhost:8000/luke-02.html
```