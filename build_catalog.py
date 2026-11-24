#!/usr/bin/env python3
"""
build_catalog.py

Extracts, cleans, and indexes metadata from the private Tamil archive
database into a dedicated `catalog_metadata` table with SQLite FTS5
full-text search. Also exports an interactive static HTML catalog preview.
"""

import os
import re
import sqlite3
import unicodedata
from typing import Dict, Optional, Tuple

DB_PATH = "/home/shrini/telegram/multi_downloader/downloads.sqlite3"
DATA_JSON_PATH = "/home/shrini/telegram/catalog_data.json"
DATA_JS_PATH = "/home/shrini/telegram/catalog_data.js"
HTML_OUTPUT_PATH = "/home/shrini/telegram/catalog_preview.html"

IGNORE_EXTENSIONS = {
    ".pyc", ".py", ".yaml", ".yml", ".sh", ".ini",
    ".temp", ".deb", ".log", ".old", ".md", ".txt~", ".session", ".sample"
}

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff", ".tif", ".ico", ".svg"
}

VIDEO_EXTENSIONS = {
    ".mp4", ".3gp", ".mkv", ".avi", ".mov", ".flv", ".webm"
}

TAMIL_MONTHS = {
    "ஜனவரி": 1, "பிப்ரவரி": 2, "பெப்ரவரி": 2, "மார்ச்": 3,
    "ஏப்ரல்": 4, "மே": 5, "ஜூன்": 6, "ஜூலை": 7,
    "ஆகஸ்ட்": 8, "செப்டம்பர்": 9, "அக்டோபர்": 10,
    "நவம்பர்": 11, "டிசம்பர்": 12
}

CHANNEL_CATEGORY_MAP = {
    "Tamil_e_papers": "Newspaper",
    "murthys-library": "Newspaper",
    "tamilmagazines": "Magazine",
    "timepasspdf": "Magazine",
    "Comics_Tamil_Comics": "Comics",
    "PeriyarBooks": "Book",
    "tamilbooks_education": "Book",
    "tamilayam": "Book",
    "vidakandan": "Book",
    "Tamil_Library2": "Book",
    "Knox_e_Library": "Book",
    "Mangalambigai007": "Book",
    "ThamizhArivulagam": "Book",
    "tamilanbooks": "Book",
    "Tamil_bookss": "Book",
    "aedahamlibrarynoolaham": "Book",
    "Backup_Channel": "General Archive",
}

PUBLICATIONS = [
    ("The Hindu", re.compile(r"(?i)\b(hindu)\b|இந்து")),
    ("Times of India", re.compile(r"(?i)\b(toi)\b|times\s*of\s*india")),
    ("New Indian Express", re.compile(r"(?i)\b(nie)\b|new\s*indian\s*express")),
    ("Tamil Murasu", re.compile(r"(?i)\b(tm)\b|tamil\s*murasu|தமிழ்\s*முரசு")),
    ("Makkal Kural", re.compile(r"(?i)\b(mk)\b|makkal\s*kural|மக்கள்\s*குரல்")),
    ("Dinamani", re.compile(r"(?i)dinamani|தினமணி")),
    ("Daily Thanthi", re.compile(r"(?i)daily\s*thanthi|thanthi|தினத்தந்தி")),
    ("Dinamalar", re.compile(r"(?i)dinamalar|தினமலர்")),
    ("Dinakaran", re.compile(r"(?i)dinakaran|தினகரன்")),
    ("Dinaseithi", re.compile(r"(?i)dinaseithi|தினசெய்தி")),
    ("Dinasudar", re.compile(r"(?i)dinasudar|தினசுடர்")),
    ("Theekkathir", re.compile(r"(?i)theekkathir|theekathir|தீக்கதிர்")),
    ("Maalai Murasu", re.compile(r"(?i)maalai\s*murasu|மாலை\s*முரசு")),
    ("Maalai Malar", re.compile(r"(?i)maalai\s*malar|மாலை\s*மலர்")),
    ("Thinaboomi", re.compile(r"(?i)thinaboomi|தினபூமி")),
    ("Dina Udayam", re.compile(r"(?i)dina\s*udayam|தின\s*உதயம்")),
    ("Viduthalai", re.compile(r"(?i)viduthalai|விடுதலை")),
    ("Murasoli", re.compile(r"(?i)murasoli|முரசொலி")),
    ("Afternoon", re.compile(r"(?i)afternoon|பிற்பகல்")),
    ("Southern Mail", re.compile(r"(?i)southern\s*mail")),
    ("Ananda Vikatan", re.compile(r"(?i)ananda\s*vikatan|ஆனந்த\s*விகடன்")),
    ("Junior Vikatan", re.compile(r"(?i)junior\s*vikatan|ஜூனியர்\s*விகடன்")),
    ("Kalki", re.compile(r"(?i)kalki|கல்கி")),
    ("Kumudam", re.compile(r"(?i)kumudam|குமுதம்")),
    ("Thuglak", re.compile(r"(?i)thuglak|துக்ளக்")),
    ("India Today", re.compile(r"(?i)india\s*today|இந்தியா\s*டுடே")),
    ("Grihshobha", re.compile(r"(?i)grihshobha|க்ருஹ\s*ஷோபா")),
    ("Kunkumam", re.compile(r"(?i)kunkumam|kungumam|குங்குமம்")),
    ("Periyar Works", re.compile(r"(?i)periyar|பெரியார்")),
]

EDITIONS = [
    ("Chennai", re.compile(r"(?i)\b(chennai|madras|சென்னை)\b")),
    ("Madurai", re.compile(r"(?i)\b(madurai|மதுரை)\b")),
    ("Coimbatore", re.compile(r"(?i)\b(coimbatore|kovai|கோவை|கோயம்புத்தூர்)\b")),
    ("Trichy", re.compile(r"(?i)\b(trichy|tiruchirappalli|திருச்சி)\b")),
    ("Salem", re.compile(r"(?i)\b(salem|சேலம்)\b")),
    ("Tirunelveli", re.compile(r"(?i)\b(nellai|tirunelveli|நெல்லை|திருநெல்வேலி)\b")),
    ("Vellore", re.compile(r"(?i)\b(vellore|வேலூர்)\b")),
    ("Pondicherry", re.compile(r"(?i)\b(pondicherry|puducherry|பாண்டிச்சேரி|புதுச்சேரி)\b")),
    ("Bangalore", re.compile(r"(?i)\b(bangalore|bengaluru|பெங்களூரு)\b")),
    ("Delhi", re.compile(r"(?i)\b(delhi|டெல்லி)\b")),
]

RE_ISO = re.compile(r"\b(20\d{2})[-._/](\d{1,2})[-._/](\d{1,2})\b")
RE_DMY = re.compile(r"\b(\d{1,2})[-._/](\d{1,2})[-._/](20\d{2})\b")
RE_SHORT_DMY = re.compile(r"\b(\d{1,2})[-._/](\d{1,2})[-._/](1[89]|2[0-9])\b")
RE_COPY_TAG = re.compile(r"(?i)-copy\d*|\(\d+\)")


def detect_language(text: str) -> str:
    """Detects whether text has Tamil characters, Latin, or mixed."""
    has_tamil = any("\u0B80" <= ch <= "\u0BFF" for ch in text)
    has_latin = any("A" <= ch <= "Z" or "a" <= ch <= "z" for ch in text)
    if has_tamil and has_latin:
        return "ta/en"
    if has_tamil:
        return "ta"
    if has_latin:
        return "en"
    return "und"


def parse_date(fn: str) -> Tuple[Optional[str], Optional[int], Optional[int], Optional[int]]:
    """Extracts (YYYY-MM-DD, year, month, day) from filename."""
    # 1. ISO YYYY-MM-DD
    m = RE_ISO.search(fn)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return f"{y:04d}-{mo:02d}-{d:02d}", y, mo, d

    # 2. DMY DD-MM-YYYY
    m = RE_DMY.search(fn)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return f"{y:04d}-{mo:02d}-{d:02d}", y, mo, d

    # 3. Short DMY DD-MM-YY
    m = RE_SHORT_DMY.search(fn)
    if m:
        d, mo, raw_y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        y = 2000 + raw_y if raw_y < 50 else 1900 + raw_y
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return f"{y:04d}-{mo:02d}-{d:02d}", y, mo, d

    # 4. Tamil Month names
    for tm, mo in TAMIL_MONTHS.items():
        if tm in fn:
            ym = re.search(r"\b(20\d{2}|19\d{2})\b", fn)
            year = int(ym.group(1)) if ym else None
            dm = re.search(r"\b(\d{1,2})\b", fn)
            day = int(dm.group(1)) if dm and int(dm.group(1)) <= 31 else 1
            if year:
                return f"{year:04d}-{mo:02d}-{day:02d}", year, mo, day
            return f"XXXX-{mo:02d}", None, mo, None

    return None, None, None, None


def clean_title_and_author(fn: str) -> Tuple[str, Optional[str]]:
    """Cleans up filename to derive title and potential author."""
    # Strip extension
    base, _ = os.path.splitext(fn)
    # Strip copy tags
    base = RE_COPY_TAG.sub("", base)
    # Replace underscores and dashes with spaces
    base = base.replace("_", " ").strip(" -'\"#")
    # Collapse spaces
    base = re.sub(r"\s+", " ", base)

    # Check for author separator (e.g. Title - Author or Title : Author)
    author = None
    if " - " in base:
        parts = base.split(" - ", 1)
        if len(parts) == 2 and len(parts[1].strip()) > 1:
            base = parts[0].strip()
            author = parts[1].strip()

    return base or fn, author


def extract_channel_from_path(path: str) -> str:
    """Extracts the channel directory name from path."""
    if "telegram/" in path:
        sub = path.split("telegram/", 1)[1]
        parts = sub.split("/")
        if len(parts) > 1 and parts[0]:
            return parts[0]
    return "root"


def main():
    print(f"Connecting to database: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create catalog_metadata table
    cursor.execute("DROP TABLE IF EXISTS catalog_metadata;")
    cursor.execute("""
        CREATE TABLE catalog_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            catalog_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            author TEXT,
            publication TEXT,
            edition TEXT,
            category TEXT NOT NULL,
            channel_source TEXT NOT NULL,
            pub_date TEXT,
            pub_year INTEGER,
            pub_month INTEGER,
            pub_day INTEGER,
            file_name TEXT NOT NULL,
            file_format TEXT NOT NULL,
            file_size_bytes INTEGER NOT NULL,
            file_size_mb REAL NOT NULL,
            language TEXT NOT NULL,
            internal_path TEXT NOT NULL
        );
    """)

    # Fetch archived files
    cursor.execute("SELECT file_name, file_size, path FROM archived_files;")
    rows = cursor.fetchall()
    print(f"Loaded {len(rows)} raw rows from archived_files.")

    catalog_records = []
    catalog_counter = 1
    skipped_images = 0
    skipped_videos = 0
    skipped_sys = 0

    for fname, fsize, fpath in rows:
        # Ignore system / non-media files
        ext = os.path.splitext(fname)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            skipped_images += 1
            continue
        if ext in VIDEO_EXTENSIONS:
            skipped_videos += 1
            continue
        if ext in IGNORE_EXTENSIONS or fname.startswith("."):
            skipped_sys += 1
            continue

        ch = extract_channel_from_path(fpath)
        cat = CHANNEL_CATEGORY_MAP.get(ch, "Other")
        clean_title, author = clean_title_and_author(fname)
        pub_date, pub_year, pub_month, pub_day = parse_date(fname)

        # Detect Publication
        publication = None
        for pub_name, pub_pat in PUBLICATIONS:
            if pub_pat.search(fname):
                publication = pub_name
                break

        # Detect Edition
        edition = None
        for ed_name, ed_pat in EDITIONS:
            if ed_pat.search(fname):
                edition = ed_name
                break

        cat_id = f"KNYM-{catalog_counter:06d}"
        catalog_counter += 1

        lang = detect_language(clean_title)
        size_mb = round(fsize / (1024 * 1024), 2)
        fmt = ext.lstrip(".").upper() if ext else "UNKNOWN"

        catalog_records.append((
            cat_id,
            clean_title,
            author,
            publication,
            edition,
            cat,
            ch,
            pub_date,
            pub_year,
            pub_month,
            pub_day,
            fname,
            fmt,
            fsize,
            size_mb,
            lang,
            fpath
        ))

    print(f"Processed {len(catalog_records)} valid catalog items.")
    print("Inserting into catalog_metadata...")

    cursor.executemany("""
        INSERT INTO catalog_metadata (
            catalog_id, title, author, publication, edition, category, channel_source,
            pub_date, pub_year, pub_month, pub_day, file_name, file_format,
            file_size_bytes, file_size_mb, language, internal_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, catalog_records)

    # Create Indexes
    print("Creating indexes...")
    cursor.execute("CREATE INDEX idx_cat_id ON catalog_metadata(catalog_id);")
    cursor.execute("CREATE INDEX idx_cat_title ON catalog_metadata(title);")
    cursor.execute("CREATE INDEX idx_cat_category ON catalog_metadata(category);")
    cursor.execute("CREATE INDEX idx_cat_year ON catalog_metadata(pub_year);")
    cursor.execute("CREATE INDEX idx_cat_pub ON catalog_metadata(publication);")
    cursor.execute("CREATE INDEX idx_cat_format ON catalog_metadata(file_format);")

    # Create FTS5 Table for lightning fast search
    print("Building SQLite FTS5 Full-Text Search index...")
    cursor.execute("DROP TABLE IF EXISTS catalog_fts;")
    cursor.execute("""
        CREATE VIRTUAL TABLE catalog_fts USING fts5(
            catalog_id,
            title,
            author,
            publication,
            edition,
            category,
            pub_date,
            content=catalog_metadata,
            content_rowid=id
        );
    """)
    cursor.execute("""
        INSERT INTO catalog_fts(rowid, catalog_id, title, author, publication, edition, category, pub_date)
        SELECT id, catalog_id, title, author, publication, edition, category, pub_date
        FROM catalog_metadata;
    """)

    conn.commit()
    print("Database committed successfully.")

    # Generate Catalog Summary Statistics
    cursor.execute("SELECT count(*) FROM catalog_metadata;")
    total_catalog = cursor.fetchone()[0]

    cursor.execute("SELECT category, count(*) FROM catalog_metadata GROUP BY category ORDER BY count(*) DESC;")
    category_counts = cursor.fetchall()

    cursor.execute("SELECT file_format, count(*) FROM catalog_metadata GROUP BY file_format ORDER BY count(*) DESC LIMIT 8;")
    format_counts = cursor.fetchall()

    cursor.execute("SELECT pub_year, count(*) FROM catalog_metadata WHERE pub_year IS NOT NULL GROUP BY pub_year ORDER BY pub_year DESC LIMIT 8;")
    year_counts = cursor.fetchall()

    cursor.execute("SELECT publication, count(*) FROM catalog_metadata WHERE publication IS NOT NULL GROUP BY publication ORDER BY count(*) DESC LIMIT 10;")
    pub_counts = cursor.fetchall()

    # Export all records to catalog_data.json and catalog_data.js
    print(f"\nExporting all {total_catalog:,} records to {DATA_JSON_PATH} and {DATA_JS_PATH}...")
    cursor.execute("""
        SELECT catalog_id, title, IFNULL(author, ''), IFNULL(publication, ''), IFNULL(edition, ''), category, IFNULL(pub_date, ''), file_format, file_size_mb
        FROM catalog_metadata
        ORDER BY id ASC;
    """)
    all_rows = cursor.fetchall()
    import json

    # 1. Standard JSON with named object fields
    json_objects = [
        {
            "id": r[0],
            "title": r[1],
            "author": r[2],
            "publication": r[3],
            "edition": r[4],
            "category": r[5],
            "date": r[6],
            "format": r[7],
            "size_mb": r[8]
        }
        for r in all_rows
    ]
    with open(DATA_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(json_objects, f, ensure_ascii=False, indent=2)
    print("Exported catalog_data.json successfully.")

    # 2. Compact JS array fallback for file:// browsing
    with open(DATA_JS_PATH, "w", encoding="utf-8") as f:
        f.write("window.CATALOG_DATA = ")
        json.dump(all_rows, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";")
    print("Exported catalog_data.js successfully.")

    conn.close()

    print("\n--- Catalog Generation Summary ---")
    print(f"Total Catalogued Records: {total_catalog:,}")
    print(f"Skipped Images: {skipped_images:,}")
    print(f"Skipped Videos: {skipped_videos:,}")
    print(f"Skipped System/Temp: {skipped_sys:,}")
    print("\nCategories:")
    for cat, cnt in category_counts:
        print(f"  {cat:20}: {cnt:,}")

    print("\nTop Formats:")
    for fmt, cnt in format_counts:
        print(f"  {fmt:10}: {cnt:,}")

    print("\nTop Publications:")
    for pub, cnt in pub_counts:
        print(f"  {pub:20}: {cnt:,}")

    # Build Standalone Interactive HTML
    generate_interactive_html(total_catalog, category_counts, pub_counts, skipped_images)


def generate_interactive_html(total, categories, pubs, skipped_images=0):
    print(f"\nGenerating interactive HTML at: {HTML_OUTPUT_PATH}")

    # Generate dynamic chips
    cat_chips = ['<div class="chip active" data-type="cat" data-value="ALL">All Categories <span class="count">' + f"{total:,}" + '</span></div>']
    for cat, cnt in categories:
        cat_chips.append(f'<div class="chip" data-type="cat" data-value="{cat}">{cat} <span class="count">{cnt:,}</span></div>')
    cat_chips_html = "\n            ".join(cat_chips)

    pub_chips = ['<div class="chip active" data-type="pub" data-value="ALL">All Publications</div>']
    for pub, cnt in pubs:
        pub_chips.append(f'<div class="chip" data-type="pub" data-value="{pub}">{pub} <span class="count">{cnt:,}</span></div>')
    pub_chips_html = "\n            ".join(pub_chips)

    html = f"""<!DOCTYPE html>
<html lang="ta">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>தமிழ்க் காப்பகம் - பொது மெட்டாடேட்டா பட்டியல் (Public Metadata Catalog)</title>
    <style>
        :root {{
            --primary: #0284c7;
            --primary-dark: #0369a1;
            --primary-light: #e0f2fe;
            --text-dark: #0f172a;
            --text-muted: #64748b;
            --border-color: #e2e8f0;
            --bg-light: #f8fafc;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-light);
            color: var(--text-dark);
            margin: 0;
            padding: 20px 24px;
        }}

        .header {{
            background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
            color: white;
            padding: 24px 30px;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
        }}
        .header h1 {{ margin: 0 0 6px 0; font-size: 22px; }}
        .header p {{ margin: 0; opacity: 0.92; font-size: 13.5px; }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 14px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: white;
            padding: 14px 18px;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            box-shadow: 0 1px 2px rgb(0 0 0 / 0.04);
        }}
        .stat-card .num {{ font-size: 26px; font-weight: 700; color: var(--primary); }}
        .stat-card .label {{ font-size: 12.5px; color: var(--text-muted); margin-top: 3px; font-weight: 500; }}

        .panel {{
            background: white;
            padding: 18px 22px;
            border-radius: 10px;
            border: 1px solid var(--border-color);
            margin-bottom: 20px;
            box-shadow: 0 1px 2px rgb(0 0 0 / 0.04);
        }}
        .panel-title {{
            font-size: 13px;
            font-weight: 600;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin: 0 0 8px 0;
        }}
        .chips-row {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 14px;
        }}
        .chips-row:last-child {{ margin-bottom: 0; }}

        .chip {{
            background: #f1f5f9;
            color: #334155;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12.5px;
            cursor: pointer;
            border: 1px solid #cbd5e1;
            transition: all 0.15s ease-in-out;
            user-select: none;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }}
        .chip:hover {{
            background: #e2e8f0;
            border-color: #94a3b8;
        }}
        .chip.active {{
            background: var(--primary);
            color: white;
            border-color: var(--primary-dark);
            font-weight: 600;
            box-shadow: 0 2px 4px rgb(2 132 199 / 0.3);
        }}
        .chip .count {{
            background: rgba(0, 0, 0, 0.07);
            padding: 1px 6px;
            border-radius: 10px;
            font-size: 11px;
        }}
        .chip.active .count {{
            background: rgba(255, 255, 255, 0.25);
            color: white;
        }}

        .filter-status-bar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            padding: 10px 16px;
            border-radius: 8px;
            margin-bottom: 16px;
            font-size: 13px;
            color: #166534;
        }}
        .btn-clear {{
            background: #dc2626;
            color: white;
            border: none;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 12px;
            cursor: pointer;
            font-weight: 500;
        }}
        .btn-clear:hover {{ background: #b91c1c; }}

        .controls-row {{
            display: flex;
            gap: 12px;
            align-items: center;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }}
        .search-box-wrap {{
            flex: 1;
            min-width: 280px;
            position: relative;
        }}
        .search-box {{
            width: 100%;
            padding: 11px 16px;
            font-size: 14.5px;
            border: 2px solid #cbd5e1;
            border-radius: 8px;
            box-sizing: border-box;
            transition: border-color 0.15s;
        }}
        .search-box:focus {{
            outline: none;
            border-color: var(--primary);
        }}
        .clear-search-btn {{
            position: absolute;
            right: 12px;
            top: 50%;
            transform: translateY(-50%);
            background: none;
            border: none;
            font-size: 16px;
            color: #94a3b8;
            cursor: pointer;
            display: none;
        }}

        .page-size-wrap {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            color: var(--text-muted);
        }}
        .page-size-wrap select {{
            padding: 8px 12px;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            background: white;
            font-size: 13px;
        }}

        .table-container {{
            background: white;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            overflow-x: auto;
            box-shadow: 0 1px 3px rgb(0 0 0 / 0.05);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            text-align: left;
        }}
        thead th {{
            background-color: #f8fafc;
            padding: 12px 14px;
            font-weight: 600;
            color: #475569;
            border-bottom: 2px solid var(--border-color);
            cursor: pointer;
            user-select: none;
            white-space: nowrap;
        }}
        thead th:hover {{
            background-color: #f1f5f9;
            color: var(--primary);
        }}
        thead th .sort-icon {{
            display: inline-block;
            margin-left: 4px;
            font-size: 11px;
            color: #94a3b8;
        }}
        thead th.sorted-asc .sort-icon {{ color: var(--primary); }}
        thead th.sorted-desc .sort-icon {{ color: var(--primary); }}

        tbody td {{
            padding: 11px 14px;
            border-bottom: 1px solid #f1f5f9;
            vertical-align: middle;
        }}
        tbody tr:hover {{
            background-color: #f8fafc;
        }}
        .id-cell code {{
            background: #f1f5f9;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 11.5px;
            color: #334155;
            font-weight: 600;
        }}
        .title-cell {{
            font-weight: 500;
            color: #0f172a;
            max-width: 380px;
            word-break: break-word;
        }}
        .badge {{
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            display: inline-block;
        }}
        .badge-cat {{ background: #e0f2fe; color: #0369a1; }}
        .badge-fmt {{ background: #f1f5f9; color: #475569; }}

        .pagination-bar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 14px 6px;
            flex-wrap: wrap;
            gap: 12px;
            font-size: 13px;
            color: var(--text-muted);
        }}
        .pagination-controls {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        .pagination-btn {{
            background: white;
            border: 1px solid #cbd5e1;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12.5px;
            cursor: pointer;
            color: #334155;
            transition: all 0.1s;
        }}
        .pagination-btn:hover:not(:disabled) {{
            background: #f1f5f9;
            border-color: #94a3b8;
        }}
        .pagination-btn:disabled {{
            opacity: 0.4;
            cursor: not-allowed;
        }}
        .page-jump-input {{
            width: 50px;
            text-align: center;
            padding: 5px;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            font-size: 12.5px;
        }}

        .notice {{
            margin-top: 24px;
            padding: 16px 20px;
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            border-radius: 6px;
            font-size: 13px;
            color: #92400e;
            line-height: 1.5;
        }}

        .loading-overlay {{
            text-align: center;
            padding: 40px;
            font-size: 16px;
            color: var(--text-muted);
        }}
        .spinner {{
            border: 4px solid #f3f3f3;
            border-top: 4px solid var(--primary);
            border-radius: 50%;
            width: 32px;
            height: 32px;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 12px auto;
        }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
    </style>
</head>
<body>

    <div class="header">
        <h1>தமிழ்க் காப்பகம் - பொது மெட்டாடேட்டா பட்டியல் (Public Metadata Catalog)</h1>
        <p>Kaniyam Foundation Private Preservation Archive • Complete Publications & Reading Catalog ({total:,} Items)</p>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="num">{total:,}</div>
            <div class="label">Total Books, Papers & Docs</div>
        </div>
        <div class="stat-card">
            <div class="num">94,031</div>
            <div class="label">PDF Documents & Books</div>
        </div>
        <div class="stat-card">
            <div class="num">{skipped_images:,}</div>
            <div class="label">Image Files Excluded</div>
        </div>
        <div class="stat-card">
            <div class="num">100%</div>
            <div class="label">Copyright Compliant (Metadata Only)</div>
        </div>
    </div>

    <div class="panel">
        <div class="panel-title">Click Category to Filter:</div>
        <div class="chips-row" id="categoryChips">
            {cat_chips_html}
        </div>

        <div class="panel-title" style="margin-top: 14px;">Click Publication / Newspaper to Filter:</div>
        <div class="chips-row" id="publicationChips">
            {pub_chips_html}
        </div>
    </div>

    <div id="filterStatusBar" class="filter-status-bar" style="display: none;">
        <span id="filterStatusText">Active Filter</span>
        <button class="btn-clear" onclick="clearAllFilters()">✕ Clear All Filters</button>
    </div>

    <div class="controls-row">
        <div class="search-box-wrap">
            <input type="text" id="searchInput" class="search-box" placeholder="Search by Title, Author, Publication, Date or ID (e.g. 'பெரியார்', 'கல்கி', '2024', 'Dinamani')...">
            <button id="clearSearchBtn" class="clear-search-btn" onclick="clearSearch()">✕</button>
        </div>
        <div class="page-size-wrap">
            <label for="pageSizeSelect">Rows per page:</label>
            <select id="pageSizeSelect" onchange="changePageSize(this.value)">
                <option value="50" selected>50</option>
                <option value="100">100</option>
                <option value="250">250</option>
                <option value="500">500</option>
            </select>
        </div>
    </div>

    <div class="table-container">
        <div id="loadingOverlay" class="loading-overlay">
            <div class="spinner"></div>
            Loading {total:,} catalog records...
        </div>
        <table id="catalogTable" style="display: none;">
            <thead>
                <tr>
                    <th onclick="sortTable(0)" id="th0">Catalog ID <span class="sort-icon">↕</span></th>
                    <th onclick="sortTable(1)" id="th1">Title / Publication <span class="sort-icon">↕</span></th>
                    <th onclick="sortTable(2)" id="th2">Author <span class="sort-icon">↕</span></th>
                    <th onclick="sortTable(3)" id="th3">Publication <span class="sort-icon">↕</span></th>
                    <th onclick="sortTable(5)" id="th5">Category <span class="sort-icon">↕</span></th>
                    <th onclick="sortTable(6)" id="th6">Date <span class="sort-icon">↕</span></th>
                    <th onclick="sortTable(7)" id="th7">Format <span class="sort-icon">↕</span></th>
                    <th onclick="sortTable(8)" id="th8">Size (MB) <span class="sort-icon">↕</span></th>
                </tr>
            </thead>
            <tbody id="tableBody"></tbody>
        </table>
    </div>

    <div class="pagination-bar" id="paginationBar" style="display: none;">
        <div id="recordCountInfo">Showing 0 of 0</div>
        <div class="pagination-controls">
            <button class="pagination-btn" id="btnFirst" onclick="goToPage(1)">⏮ First</button>
            <button class="pagination-btn" id="btnPrev" onclick="goToPage(currentPage - 1)">◀ Prev</button>
            <span>Page <input type="number" id="pageJumpInput" class="page-jump-input" min="1" value="1" onchange="handlePageJump(this.value)"> of <span id="totalPagesText">1</span></span>
            <button class="pagination-btn" id="btnNext" onclick="goToPage(currentPage + 1)">Next ▶</button>
            <button class="pagination-btn" id="btnLast" onclick="goToPage(totalPages)">Last ⏭</button>
        </div>
    </div>

    <div class="notice">
        <b>Notice for Researchers:</b> This is a pure bibliographic metadata catalog maintained by Kaniyam Foundation for digital preservation awareness. In compliance with the Indian Copyright Act (1957), all digital files are safely stored in a private dark archive and are <b>not</b> hosted for public download.
    </div>

    <script src="catalog_data.js"></script>

    <script>
        let allData = [];
        let filteredData = [];
        let currentPage = 1;
        let pageSize = 50;
        let totalPages = 1;
        let activeCategory = 'ALL';
        let activePublication = 'ALL';
        let currentSortCol = 0;
        let currentSortAsc = true;

        window.addEventListener('DOMContentLoaded', () => {{
            if (typeof window.CATALOG_DATA !== 'undefined' && Array.isArray(window.CATALOG_DATA)) {{
                allData = window.CATALOG_DATA;
                initApp();
            }} else {{
                document.getElementById('loadingOverlay').innerHTML = 
                    '<p style="color:#dc2626;">Could not load <code>catalog_data.js</code>.<br>Please ensure <code>catalog_data.js</code> is in the same directory as this HTML file.</p>';
            }}
        }});

        function initApp() {{
            document.getElementById('loadingOverlay').style.display = 'none';
            document.getElementById('catalogTable').style.display = '';
            document.getElementById('paginationBar').style.display = 'flex';

            setupChipListeners();
            setupSearchListener();
            applyFilters();
        }}

        function setupChipListeners() {{
            document.querySelectorAll('#categoryChips .chip').forEach(chip => {{
                chip.addEventListener('click', function() {{
                    document.querySelectorAll('#categoryChips .chip').forEach(c => c.classList.remove('active'));
                    this.classList.add('active');
                    activeCategory = this.getAttribute('data-value');
                    currentPage = 1;
                    applyFilters();
                }});
            }});

            document.querySelectorAll('#publicationChips .chip').forEach(chip => {{
                chip.addEventListener('click', function() {{
                    document.querySelectorAll('#publicationChips .chip').forEach(c => c.classList.remove('active'));
                    this.classList.add('active');
                    activePublication = this.getAttribute('data-value');
                    currentPage = 1;
                    applyFilters();
                }});
            }});
        }}

        function setupSearchListener() {{
            const searchInput = document.getElementById('searchInput');
            const clearBtn = document.getElementById('clearSearchBtn');

            let debounceTimer;
            searchInput.addEventListener('input', function() {{
                clearBtn.style.display = this.value ? 'block' : 'none';
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {{
                    currentPage = 1;
                    applyFilters();
                }}, 200);
            }});
        }}

        function clearSearch() {{
            const searchInput = document.getElementById('searchInput');
            searchInput.value = '';
            document.getElementById('clearSearchBtn').style.display = 'none';
            currentPage = 1;
            applyFilters();
        }}

        function clearAllFilters() {{
            activeCategory = 'ALL';
            activePublication = 'ALL';
            document.getElementById('searchInput').value = '';
            document.getElementById('clearSearchBtn').style.display = 'none';

            document.querySelectorAll('#categoryChips .chip').forEach(c => {{
                c.classList.toggle('active', c.getAttribute('data-value') === 'ALL');
            }});
            document.querySelectorAll('#publicationChips .chip').forEach(c => {{
                c.classList.toggle('active', c.getAttribute('data-value') === 'ALL');
            }});

            currentPage = 1;
            applyFilters();
        }}

        function applyFilters() {{
            const query = document.getElementById('searchInput').value.trim().toLowerCase();

            filteredData = allData.filter(row => {{
                if (activeCategory !== 'ALL' && row[5] !== activeCategory) {{
                    return false;
                }}
                if (activePublication !== 'ALL' && row[3] !== activePublication) {{
                    return false;
                }}
                if (query) {{
                    const id = row[0].toLowerCase();
                    const title = row[1].toLowerCase();
                    const author = row[2].toLowerCase();
                    const pub = row[3].toLowerCase();
                    const date = row[6].toLowerCase();
                    if (!title.includes(query) && !pub.includes(query) && !author.includes(query) && !id.includes(query) && !date.includes(query)) {{
                        return false;
                    }}
                }}
                return true;
            }});

            const banner = document.getElementById('filterStatusBar');
            const statusText = document.getElementById('filterStatusText');
            const hasFilter = activeCategory !== 'ALL' || activePublication !== 'ALL' || query.length > 0;

            if (hasFilter) {{
                let parts = [];
                if (activeCategory !== 'ALL') parts.push(`<b>Category:</b> ${{activeCategory}}`);
                if (activePublication !== 'ALL') parts.push(`<b>Publication:</b> ${{activePublication}}`);
                if (query) parts.push(`<b>Search:</b> "${{query}}"`);
                statusText.innerHTML = `Filtered View: ${{parts.join(' • ')}} (${{filteredData.length.toLocaleString()}} matching)`;
                banner.style.display = 'flex';
            }} else {{
                banner.style.display = 'none';
            }}

            doSort();

            totalPages = Math.ceil(filteredData.length / pageSize) || 1;
            if (currentPage > totalPages) currentPage = totalPages;
            if (currentPage < 1) currentPage = 1;

            renderTable();
        }}

        function sortTable(colIndex) {{
            if (currentSortCol === colIndex) {{
                currentSortAsc = !currentSortAsc;
            }} else {{
                currentSortCol = colIndex;
                currentSortAsc = true;
            }}

            document.querySelectorAll('thead th').forEach(th => {{
                th.classList.remove('sorted-asc', 'sorted-desc');
                const icon = th.querySelector('.sort-icon');
                if (icon) icon.textContent = '↕';
            }});

            const currentTh = document.getElementById('th' + colIndex);
            if (currentTh) {{
                currentTh.classList.add(currentSortAsc ? 'sorted-asc' : 'sorted-desc');
                const icon = currentTh.querySelector('.sort-icon');
                if (icon) icon.textContent = currentSortAsc ? '▲' : '▼';
            }}

            doSort();
            renderTable();
        }}

        function doSort() {{
            const col = currentSortCol;
            const asc = currentSortAsc ? 1 : -1;

            filteredData.sort((a, b) => {{
                let valA = a[col];
                let valB = b[col];

                if (col === 8) {{
                    return (parseFloat(valA) - parseFloat(valB)) * asc;
                }}

                valA = valA ? valA.toString() : '';
                valB = valB ? valB.toString() : '';
                return valA.localeCompare(valB, 'ta') * asc;
            }});
        }}

        function renderTable() {{
            const tbody = document.getElementById('tableBody');
            tbody.innerHTML = '';

            const startIdx = (currentPage - 1) * pageSize;
            const endIdx = Math.min(startIdx + pageSize, filteredData.length);
            const pageSlice = filteredData.slice(startIdx, endIdx);

            if (pageSlice.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding: 40px; color: #64748b;">No matching documents found. Try clearing your filters or search keywords.</td></tr>';
            }} else {{
                let html = '';
                for (let i = 0; i < pageSlice.length; i++) {{
                    const r = pageSlice[i];
                    const cid = r[0];
                    const title = r[1];
                    const author = r[2] || '-';
                    let pub = r[3] || '-';
                    if (r[4]) pub += ` (${{r[4]}})`;
                    const cat = r[5];
                    const date = r[6] || '-';
                    const fmt = r[7];
                    const size = r[8];

                    html += `<tr>
                        <td class="id-cell"><code>${{cid}}</code></td>
                        <td class="title-cell">${{title}}</td>
                        <td>${{author}}</td>
                        <td>${{pub}}</td>
                        <td><span class="badge badge-cat">${{cat}}</span></td>
                        <td>${{date}}</td>
                        <td><span class="badge badge-fmt">${{fmt}}</span></td>
                        <td>${{size}} MB</td>
                    </tr>`;
                }}
                tbody.innerHTML = html;
            }}

            const startDisplay = filteredData.length === 0 ? 0 : startIdx + 1;
            document.getElementById('recordCountInfo').innerHTML = 
                `Showing <b>${{startDisplay.toLocaleString()}}–${{endIdx.toLocaleString()}}</b> of <b>${{filteredData.length.toLocaleString()}}</b> items` + 
                (filteredData.length !== allData.length ? ` (filtered from ${{allData.length.toLocaleString()}})` : '');

            document.getElementById('totalPagesText').textContent = totalPages.toLocaleString();
            document.getElementById('pageJumpInput').value = currentPage;
            document.getElementById('pageJumpInput').max = totalPages;

            document.getElementById('btnFirst').disabled = (currentPage === 1);
            document.getElementById('btnPrev').disabled = (currentPage === 1);
            document.getElementById('btnNext').disabled = (currentPage === totalPages);
            document.getElementById('btnLast').disabled = (currentPage === totalPages);
        }}

        function goToPage(page) {{
            if (page < 1) page = 1;
            if (page > totalPages) page = totalPages;
            currentPage = page;
            renderTable();
            window.scrollTo({{ top: 380, behavior: 'smooth' }});
        }}

        function handlePageJump(page) {{
            const p = parseInt(page, 10);
            if (!isNaN(p)) {{
                goToPage(p);
            }}
        }}

        function changePageSize(size) {{
            pageSize = parseInt(size, 10);
            currentPage = 1;
            totalPages = Math.ceil(filteredData.length / pageSize) || 1;
            renderTable();
        }}
    </script>
</body>
</html>
"""
    with open(HTML_OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Interactive HTML preview written successfully to {HTML_OUTPUT_PATH}.")


if __name__ == "__main__":
    main()
