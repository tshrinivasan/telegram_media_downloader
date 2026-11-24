# Private Archive Management & Public Metadata Catalog Guide

**Project:** Contemporary Tamil Digital Preservation Archive  
**Organization:** Kaniyam Foundation  
**Lead:** T Shrinivasan  
**Last Updated:** November 2024 / Production Status  

---

## 1. Overview & Core Architecture

Preserving contemporary Tamil newspapers, magazines, books, and e-papers presents two competing requirements:
1. **Long-Term Preservation:** Safeguarding massive daily downloads from ephemeral social media channels into a secure, durable archive.
2. **Legal & Copyright Compliance:** Ensuring copyrighted contemporary works (newspapers, magazines, modern books) are **never publicly distributed or leaked**, while providing researchers and the public with a lawful discovery mechanism.

To solve this, the archive operates on a **Two-Tier Architecture**:

```
+-------------------------------------------------------------------------+
|                         TIER 1: PUBLIC DISCOVERY                        |
|  - Public Searchable Metadata Catalog (Titles, Dates, Authors, Formats)  |
|  - Available formats: catalog_preview.html, catalog_data.json           |
|  - ZERO downloadable payload files / ZERO direct server links           |
|  - 100% legal under Indian Copyright Law (factual bibliographic data)   |
+-------------------------------------------------------------------------+
                                    |
                           [Controlled Access]
                                    v
+-------------------------------------------------------------------------+
|                       TIER 2: PRIVATE DARK ARCHIVE                      |
|  - Hardened remote storage (InterServer ST 300/ST 400 + Cold Backups)   |
|  - Direct web access strictly blocked (HTTP 403 Forbidden)              |
|  - Access restricted to authorized administrators via rsync / SFTP / SSH|
+-------------------------------------------------------------------------+
```

---

## 2. Server Security & Leak Prevention

During a defensive security audit of the remote storage server (`69.10.39.2` / `st34220.ispot.cc`), it was discovered that storing files inside the web root (`public_html/kaniyam-ftp/telegram`) allowed unauthenticated users to download full copyrighted PDFs over HTTP/HTTPS if they knew or guessed the filename.

### Hardening Applied
1. **Web Access Disabled via `.htaccess`:**
   A root `.htaccess` rule was deployed inside `/home/st34220/public_html/kaniyam-ftp/`:
   ```apache
   Order Deny,Allow
   Deny from all
   Require all denied
   ```
2. **Audit Verification:**
   * Tested direct URL requests (e.g., `https://st34220.ispot.cc/kaniyam-ftp/telegram/.../Hindu_Chennai_20-08-2024.pdf`).
   * **Result:** All web requests now strictly return **`HTTP 403 Forbidden`**.
   * **Administrative protocols:** `rsync`, SSH, and SFTP remain 100% operational because they bypass HTTP.
3. **Long-Term Recommendation:**
   Move archival folders completely outside `public_html/` (e.g., to `/home/st34220/archive/`) to make web exposure physically impossible.

---

## 3. Metadata Extraction Pipeline (`build_catalog.py`)

The automated script [`build_catalog.py`](file:///home/shrini/telegram/multi_downloader/build_catalog.py) extracts and cleans metadata from the unified SQLite database (`downloads.sqlite3`) without modifying raw archive files.

### Catalog Sizing (Images Excluded)
To focus purely on text publications and reading materials, images and video files are filtered out:
* **Total Cataloged Records:** **95,919** items
* **Images Skipped:** 32,613 (.jpg, .jpeg, .png, .webp, .gif)
* **Videos Skipped:** 446 (.mp4, .3gp)
* **System/Temp Files Skipped:** 1,490 (.pyc, .yaml, .sh, .temp)

### Category Distribution
* **Books:** 69,171
* **Newspapers (e-papers):** 17,782
* **Magazines:** 6,484
* **Comics:** 1,090
* **General Archive:** 1,358
* **Other Documents:** 34

### Automated Metadata Parsing
* **Clean Titles:** Strips extensions, copy tags (`-copy1`, `(1)`), and formatting artifacts.
* **Author Parsing:** Separates `Title - Author` patterns.
* **Publication Detection:** Identifies major publications (*Dinamani*, *Maalai Murasu*, *Dinakaran*, *Thinaboomi*, *Tamil Murasu*, *Kumudam*, *Daily Thanthi*, *The Hindu*, *Times of India*, etc.).
* **Edition Detection:** Maps geographic editions (*Chennai*, *Madurai*, *Coimbatore*, *Trichy*, etc.).
* **Date Normalization:** Extracts and normalizes publication dates to `YYYY-MM-DD` from English and Tamil formats (including Tamil month names: `ஜனவரி`, `பிப்ரவரி`, `மார்ச்`, etc.).
* **Language Classification:** Detects Tamil script (`ta`), English (`en`), or bilingual (`ta/en`).

### Full-Text Search (SQLite FTS5)
The pipeline automatically generates a virtual full-text search table (`catalog_fts`) inside `downloads.sqlite3`:
* Sub-millisecond queries (< 1 ms) across 95,919 records in both Tamil and English.
* Example queries: `"பெரியார்"` (0.88 ms), `"விகடன்"` (0.23 ms), `"Dinamani"` (0.15 ms).

---

## 4. Public Catalog Artifacts

Running `python3 build_catalog.py` produces two ready-to-publish assets:

### 1. `catalog_data.json` (Universal Data File)
Located at [`/home/shrini/telegram/catalog_data.json`](file:///home/shrini/telegram/catalog_data.json). Contains the entire 95,919-record catalog formatted as standard JSON objects:
```json
{
  "id": "KNYM-000002",
  "title": "Chennai TM 26-08-2024",
  "author": "",
  "publication": "Tamil Murasu",
  "edition": "Chennai",
  "category": "Newspaper",
  "date": "2024-08-26",
  "format": "PDF",
  "size_mb": 1.55
}
```

### 2. `catalog_preview.html` (Interactive Web Browser)
Located at [`/home/shrini/telegram/catalog_preview.html`](file:///home/shrini/telegram/catalog_preview.html). A self-contained, responsive web application offering:
* **Clickable Top Chips:** One-click filtering by Category (*Books*, *Newspapers*, *Magazines*) or Publication (*Dinamani*, *Kumudam*, *The Hindu*).
* **Sortable Columns:** Ascending/Descending sorting on Catalog ID, Title, Author, Publication, Category, Date, Format, and Size. Supports Tamil alphabetical collation (`ta`).
* **Pagination Controls:** Instant pagination with page sizes of 50, 100, 250, or 500 rows, plus direct page jumping.
* **Instant Search:** Debounced multi-field search box with a clear button.
* **Dual-Mode Loading:** Uses asynchronous `fetch('catalog_data.json')` when served over HTTP/HTTPS, with an automatic fallback to `catalog_data.js` when opened locally via `file:///` in Google Chrome (avoiding CORS blocks).

---

## 5. Storage Economics & Roadmap Summary

Full pricing and infrastructure comparisons are detailed in [`server-pricing.md`](file:///home/shrini/telegram/multi_downloader/server-pricing.md):

* **Immediate Term (Current Baseline):**
  * Current plan: InterServer ST 300 (2 TB @ $8/mo).
  * Recommended upgrade: **InterServer ST 400 (4 TB @ $10/mo)** — doubles capacity for +$2/mo with **zero migration effort**.
* **Cold Disaster Vault (Secondary Backup):**
  * **AWS S3 Glacier Deep Archive:** **$1.01 per TB / month**.
  * Storing 10 TB costs only ~$10.10/mo (~₹850/mo), providing a permanent, indestructible offsite preservation copy.
* **Large Scale (20 TB – 40 TB+):**
  * **Hetzner Server Auction:** Dedicated bare-metal servers with 20–40 TB usable storage for **€35 – €45/month** (~$1.00 – $1.50 / TB / mo) with full Linux root access for running downloaders and OCR indexing directly.

---

## 6. Copyright Guidelines & Access Policy

1. **Metadata is Public Information:** Bibliographic facts (titles, dates, volume numbers, publication names, authors) are not protected by copyright and can be freely published online.
2. **Dark Archive Security:** Payload files (PDFs, EPUBs) are kept private and never exposed via public download links.
3. **Scholarly Fair Dealing (Section 52(1)(a)):**
   * Do not provide open file request services or public Telegram bots.
   * If an academic scholar requires an out-of-print historical document for non-commercial research, follow the **Roja Muthiah Research Library (RMRL)** model: individual, non-commercial, single-session reference access.

---

## 7. Duplicate Prevention & File Integrity Pipeline

To avoid duplicate downloads (`-copy1`, `-copy2`) and prevent broken 0-byte corrupt stub files, `media_downloader.py` and `utils/file_management.py` implement a 4-tier deduplication check:

1. **Database Pre-Check (`db.is_archived_or_downloaded`):**
   * Before initiating a download, matches the Telegram filename and exact byte size against the SQLite `archived_files` and `download_history` tables.
   * If present, skips the download immediately with zero network overhead.

2. **Local Disk Size & Copy Match:**
   * Scans the target folder for the canonical name and sibling copies matching `^{base_stem}(-copy\d+)?{ext}$`.
   * If an existing file has the exact matching `file_size`, marks it as existing, records it in `download_history`, and skips downloading.
   * Distinguishes between duplicate posts (skipped) vs. genuine multi-volume books sharing the same name but differing in size (e.g., *சாம்பசிவம் பிள்ளை* Dictionary Vol 1, 2, 3).

3. **0-Byte and Incomplete Stub Cleanup:**
   * Removes any 0-byte corrupt stub files left behind by aborted downloads (e.g., from low disk space circuit breakers) rather than letting them trigger `get_next_name` into `-copy1`.
   * Cleans up incomplete files (`0 < size < expected`) automatically if a download is interrupted by an exception or network error.

4. **Chunked MD5 Deduplication (`manage_duplicate_file`):**
   * Verifies byte size first before hashing.
   * Uses 64 KB chunked MD5 hashing (preventing memory exhaustion on multi-GB files) only when files share the exact same byte size.
   * Retains the primary canonical name and eliminates duplicate downloaded copies.

---

## 8. Isolated Downloads Directory & Safe Purge Workflow

To keep code repositories clean and avoid accidental deletion of source code or configs:

1. **Subfolder Isolation (`all_downloads/`):**
   * All downloads automatically route into a dedicated `all_downloads/` directory (e.g., `all_downloads/edagam_library/`, `all_downloads/tamilayam/`, etc.).
   * Configurable via the global `download_directory` key in `config.yaml` (default: `"all_downloads"`).
   * Prevents dozens of downloaded channel directories from cluttering the root code workspace.

2. **Safe Sync & Purge Sequence:**
   * After downloads finish, sync the entire downloads directory to remote storage:
     ```bash
     rsync -arv --info=progress2 /home/shrini/telegram/multi_downloader/all_downloads/ st34220@69.10.39.2:/home/st34220/public_html/kaniyam-ftp/telegram/
     ```
   * Once synced, wipe all downloaded files safely with a single command:
     ```bash
     rm -rf /home/shrini/telegram/multi_downloader/all_downloads/*
     ```
   * Code, `.git`, `config.yaml`, and `downloads.sqlite3` are untouched and 100% safe.


