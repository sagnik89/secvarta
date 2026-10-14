```text
███████╗███████╗ ██████╗██╗   ██╗ █████╗ ██████╗ ████████╗ █████╗
██╔════╝██╔════╝██╔════╝██║   ██║██╔══██╗██╔══██╗╚══██╔══╝██╔══██╗
███████╗█████╗  ██║     ██║   ██║███████║██████╔╝   ██║   ███████║
╚════██║██╔══╝  ██║     ██║   ██║██╔══██╗██╔══██╗   ██║   ██╔══██║
███████║███████╗╚██████╗╚██████╔╝██║  ██║██║  ██║   ██║   ██║  ██║
╚══════╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝
```

<p align="center">
  <b>Cybersecurity intelligence, connected.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.14%2B-3776AB?style=flat&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Package_Manager-uv-DE5FE9?style=flat" alt="uv">
  <img src="https://img.shields.io/badge/Database-SQLite-003B57?style=flat&logo=sqlite&logoColor=white" alt="SQLite">
  <img src="https://img.shields.io/badge/ORM-SQLAlchemy-D71F00?style=flat" alt="SQLAlchemy">
  <img src="https://img.shields.io/badge/Notifications-Discord-5865F2?style=flat&logo=discord&logoColor=white" alt="Discord">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License">
</p>

> A lightweight cybersecurity intelligence aggregator that collects security news, extracts CVE references, stores structured vulnerability data, and delivers daily digests through Discord.

> **SecVarta** combines *Sec* (Security) and *Varta* (वार्ता), a word associated with news, conversation, and information in Indian languages.


## The Problem

Cybersecurity news is scattered across multiple publications, security blogs, and vulnerability reporting sources.

Keeping track of emerging threats, identifying vulnerabilities mentioned across different articles, and revisiting relevant security updates can quickly become a repetitive manual task.

Security enthusiasts, researchers, and developers need a structured way to collect and organize this information without constantly checking every source individually.

## How SecVarta Solves It

SecVarta automates cybersecurity intelligence collection through a modular Python data pipeline.

- **Feed ingestion:** Fetches entries from configured RSS and Atom feeds.
- **Metadata normalization:** Converts source-specific entries into a consistent article representation.
- **CVE extraction:** Identifies CVE identifiers in available article metadata.
- **Persistent storage:** Stores articles, CVEs, and their relationships in SQLite using SQLAlchemy.
- **Structured output:** Supports structured data for downstream processing and integrations.
- **Discord notifications:** Generates a daily digest and delivers security news summaries through Discord.

The modular design separates ingestion, persistence, and notifications, making it easier to extend the pipeline with additional sources and consumers.

## Installation

### Prerequisites

- Python version supported by `pyproject.toml`
- [uv](https://docs.astral.sh/uv/)
- Git

### 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd SecVarta
```

### 2. Install dependencies

Sync the project environment using `uv`:

```bash
uv sync
```

This creates or updates the virtual environment and installs the project dependencies specified by `pyproject.toml` and `uv.lock`.

### 3. Configure the .env

Add your discord webhook url

Add the database url


### 3. Run SecVarta

Run the CLI through `uv`:

```bash
uv run python -m secvarta --help
```

## Database Design

SecVarta uses SQLite with SQLAlchemy to persist collected intelligence in `data/secvarta.db`.

The core data model consists of:

- **Articles:** Stores normalized article metadata.
- **CVEs:** Stores unique vulnerability identifiers.
- **Article–CVE relationships:** A junction table supports the many-to-many relationship between articles and CVEs.

This structure allows one article to reference multiple CVEs and one CVE to appear in multiple articles without duplicating vulnerability records.

## Project Structure

```text
SecVarta/
├── data/
│   └── secvarta.db
├── src/
│   └── secvarta/
│       ├── cli.py
│       ├── database/
│       │   ├── connection.py
│       │   ├── models.py
│       │   ├── repository.py
│       │   └── schemas.py
│       ├── ingestion/
│       │   ├── fetcher.py
│       │   ├── parser.py
│       │   ├── normalizer.py
│       │   ├── cve_extractor.py
│       │   ├── urls.py
│       │   └── service.py
│       └── notifications/
│           ├── digest.py
│           └── discord.py
├── pyproject.toml
├── uv.lock
├── README.md
└── LICENSE
```

## Workflow

1. **Fetch:** Retrieve entries from configured RSS/Atom feeds.
2. **Parse and normalize:** Convert feed entries into a consistent representation.
3. **Extract:** Identify CVE identifiers in available article metadata.
4. **Persist:** Store articles, CVEs, and their relationships in SQLite.
5. **Prepare digest:** Generate a summary of relevant security news.
6. **Notify:** Deliver the digest through the Discord integration.

The ingestion, database, and notification layers are separate components. This keeps the core pipeline independent of the notification destination and makes future integrations easier to introduce.

## TODO

- [ ] Improve feed failure handling, timeouts, and duplicate detection.
- [ ] Add structured logging and clearer ingestion reports.
- [ ] Introduce a systemd service and **systemd timer** for scheduled ingestion on Linux.
- [ ] Expose collected intelligence through a read-only API.
- [ ] Build a web interface for browsing articles and CVE relationships.
- [ ] Expand notification options and filtering for relevant security updates.

## License

SecVarta is released under the [MIT License](LICENSE).
