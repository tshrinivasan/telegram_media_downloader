# Remote Storage Cost Comparison & Architecture Guide

**Project:** Private Archive for Contemporary Tamil Digital Files (Kaniyam Foundation)  
**Last Updated:** November 2024 / Current Review  
**Author / Maintainer:** T Shrinivasan / Kaniyam Foundation  

---

## 1. Executive Summary & Current Baseline

The archive currently holds **~145,000 files (~1.6 to 1.78 TB)** of contemporary Tamil newspapers, magazines, books, and e-papers. As daily automated ingestion continues from 30+ Telegram channels, the storage requirement will expand into:
* **Near-Term (6–12 months):** 3 TB – 5 TB
* **Mid-Term (1–3 years):** 10 TB – 20 TB
* **Long-Term Preservation:** 50 TB+

### Current Live Production Setup
* **Provider:** [InterServer Storage Hosting](https://www.interserver.net/storage/#plans)
* **Plan:** ST 300
* **Allocated Capacity:** 2 TB
* **Monthly Cost:** $8.00 USD / month (~₹670 INR/mo)
* **Access Protocols:** Non-root SSH, rsync, SFTP, SCP, DirectAdmin
* **Web Delivery:** Apache HTTP/HTTPS (`public_html/kaniyam-ftp/telegram`)

---

## 2. Comprehensive Cost & Provider Comparison

| Provider & Tier | Storage Type | Capacity | Cost / Month | Cost / TB / Mo | Protocols & Features | Best Fit For |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **AWS S3 Glacier Deep Archive** | Cold Tape Object | Any (Pay-as-you-go) | **$1.01 / TB** | **$1.01** (~₹85) | S3 API, `rclone`, AWS CLI. 12–48 hr retrieval window. | **Secondary off-site disaster recovery vault** |
| **OVHcloud Cold Archive** | Cold Tape Object | Any (Pay-as-you-go) | **~$1.40 / TB** | **~$1.40** (€1.33) | S3-compatible, asynchronous tape retrieval. | Alternative cold backup in EU |
| **ServaRICA (Polar Bear)** | Storage VPS (HDD) | 2 TB | **$5.00** ($48/yr = $4) | **$2.00 – $2.50** | Full Linux Root, RAID-Z2, unmetered 250Mbps, rsync, HTTP. | Low-cost 2 TB VPS with full root access |
| **ServaRICA (Killer Whale / Mammoth)** | Storage VPS (HDD) | 3.5 TB / 8 TB | **$8.50 / $20.00** | **$2.29 – $2.43** | Full Linux Root, RAID-Z2, unmetered bandwidth. | Budget VPS scaling up to 8 TB |
| **InterServer Storage VPS** | Storage VPS (HDD) | 2 TB (2 slices) | **$6.00** | **$3.00** | Full Linux Root, 4 GB RAM, 4 TB transfer. | Root-access alternative on InterServer |
| **InterServer ST 400** | Shared Storage | **4 TB** | **$10.00** | **$2.50** | rsync, SSH, DirectAdmin, Apache HTTP public web links. | **Immediate frictionless 4 TB upgrade** |
| **InterServer ST 500** | Shared Storage | **10 TB** | **$25.00** | **$2.50** | rsync, SSH, DirectAdmin, 15 TB transfer. | Direct scaling without data migration |
| **InterServer ST 600** | Shared Storage | **20 TB** | **$42.00** | **$2.10** | rsync, SSH, DirectAdmin, 20 TB transfer. | Direct scaling up to 20 TB |
| **Hetzner Storage Box (BX21)** | Managed Storage | 5 TB | **~€10.90** (~$11.80) | **~$2.36** | rsync, SFTP, WebDAV, Borg, 20 snapshots, unlimited traffic. | Managed backup box with automated snapshots |
| **Hetzner Storage Box (BX31)** | Managed Storage | 10 TB | **~€20.80** (~$22.50) | **~$2.25** | rsync, SFTP, WebDAV, Borg, 30 snapshots, unlimited traffic. | Managed 10 TB storage box |
| **Hetzner Storage Box (BX41)** | Managed Storage | 20 TB | **~€40.60** (~$44.00) | **~$2.20** | rsync, SFTP, WebDAV, Borg, 40 snapshots, unlimited traffic. | Managed 20 TB storage box |
| **Hetzner Server Auction (Dedicated)** | Bare-Metal Server | 20 TB – 40 TB | **€35 – €45** (~$38 – $48) | **$1.00 – $1.50** | Full Bare-Metal Root, 1Gbps unmetered, multiple 10–14TB enterprise HDDs. | **Lowest cost-per-TB at massive scale (20TB+)** |
| **iDrive e2** | S3 Object Storage | Pay-as-you-go | **$4.00 / TB** | **$4.00** | S3 API, `rclone`, free egress (up to 3x data), no API fees. | S3-compatible hot object storage |
| **Backblaze B2** | S3 Object Storage | Pay-as-you-go | **$6.95 / TB** | **$6.95** | S3 API, `rclone`, free egress (up to 3x data), 11 9s durability. | Standard hot object storage |

---

## 3. Detailed Category Analysis

### Category A: Cold Archival / Permanent Preservation (Cheapest Overall)
* **Top Pick:** **AWS S3 Glacier Deep Archive** ($1.01 / TB / month)
* **Economics:**
  * 2 TB: **$2.02 / month** (~₹170)
  * 5 TB: **$5.05 / month** (~₹425)
  * 10 TB: **$10.10 / month** (~₹850)
  * 20 TB: **$20.20 / month** (~₹1,700)
* **Strengths:** 
  * Extreme durability (99.999999999% across multiple AWS availability zones).
  * Inexpensive write-and-preserve storage.
* **Limitations:**
  * **Not for live web browsing:** Retrieval takes 12 to 48 hours.
  * **Egress & Retrieval Costs:** Retrieving data back out costs ~$0.02/GB (~$20/TB) plus AWS data transfer fees.
  * **Minimum Retention:** 180-day minimum duration commitment per object.
* **Use Case:** An immutable, offsite disaster recovery backup to guarantee digital Tamil publications survive hardware or provider failures.

---

### Category B: Shared Storage with Web/HTTP Delivery (Current Model)
* **Top Pick:** **InterServer Storage Hosting (ST 400 / ST 500)**
* **Economics:**
  * ST 400 (4 TB): **$10.00 / month** ($2.50 / TB)
  * ST 500 (10 TB): **$25.00 / month** ($2.50 / TB)
  * ST 600 (20 TB): **$42.00 / month** ($2.10 / TB)
* **Strengths:**
  * **Zero Migration Effort:** Upgrading from ST 300 (2 TB @ $8) to ST 400 (4 TB @ $10) costs only **+$2.00/month** and doubles capacity instantly with no data movement required.
  * **Native HTTP Delivery:** Built-in Apache web server (`public_html`) allows researchers to download or view PDFs directly via browser URLs.
  * **Standard Protocols:** Supports non-root SSH, rsync, SFTP, and DirectAdmin file management.
* **Limitations:**
  * Shared environment (subject to inode limits or shared I/O constraints).
  * No root access to run Python scripts or cron downloaders directly on the server.

---

### Category C: High-Capacity Storage VPS (With Root Access)
* **Top Pick:** **ServaRICA (Canada)** & **InterServer Storage VPS**
* **Economics:**
  * ServaRICA Polar Bear (2 TB): **$5.00 / month** (or **$48.00 / year = $4.00 / mo**)
  * ServaRICA Killer Whale (3.5 TB): **$8.50 / month** ($84.00 / year)
  * ServaRICA Mammoth (8 TB): **$20.00 / month** ($220.00 / year)
  * InterServer Storage VPS (2 TB): **$6.00 / month** (2 slices @ $3/slice)
* **Strengths:**
  * **Full Linux Root Access:** Can run `telegram_media_downloader`, Python scripts, and cron jobs directly on the remote server, eliminating local laptop disk usage.
  * **Enterprise File Systems:** ZFS RAID-Z2 provides data parity against bit rot and disk failures.
* **Limitations:**
  * Requires server administration (security updates, firewall, web server setup).
  * Requires moving the existing ~1.6 TB archive over the network.

---

### Category D: Dedicated Bare-Metal Servers (20 TB – 40 TB+ at Scale)
* **Top Pick:** **Hetzner Server Auction (Serverbörse - Germany / Finland)**
* **Economics:**
  * Typical configuration: 64 GB RAM, Xeon or AMD Ryzen, **2× 14 TB or 4× 10 TB Enterprise HDDs (20 TB to 40 TB usable)** for **€35 – €45 / month** (~$38 – $48 USD).
  * Effective price: **$1.00 – $1.50 per TB / month**.
* **Strengths:**
  * Dedicated hardware without noisy neighbors or shared limits.
  * Unmetered 1 Gbit/s network connection.
  * Capable of running full-text search engines (Recoll, Meilisearch, Elasticsearch) and OCR indexing for hundreds of thousands of Tamil documents.
* **Limitations:**
  * Higher minimum monthly spend ($38–$48/mo), making it economical only when data volume exceeds 15–20 TB.

---

## 4. Recommended Staged Roadmap for Kaniyam Foundation

```
[Phase 1: Now (1.6 TB - 4 TB)]
  -> Upgrade InterServer ST 300 ($8/mo) to ST 400 ($10/mo)
  -> Instant 4 TB capacity, zero migration overhead.

[Phase 2: Preservation Safeguard]
  -> Configure periodic automated sync to AWS S3 Glacier Deep Archive
  -> Cost: ~$1.00 - $4.00/mo for an immutable disaster recovery copy.

[Phase 3: Scale to 10 TB]
  -> InterServer ST 500 ($25/mo for 10 TB) OR ServaRICA Mammoth ($20/mo for 8 TB)
  -> OR Hetzner Storage Box BX31 (€20.80/mo for 10 TB).

[Phase 4: Institutional Scale (20 TB - 50 TB+)]
  -> Hetzner Dedicated Server Auction (~$40/mo for 28-40 TB)
  -> Run central downloader, full-text OCR indexing, and Tamil research web portal.
```
