# Luxembourg Real Estate Agencies Scraper

A Python web scraper that extracts real estate agency information from the [Chambre Immobilière du Grand-Duché de Luxembourg](https://www.chambre-immobiliere.lu/) and stores it in a local SQLite database with CSV export capability.

## Features

- 🔍 **Comprehensive Scraping**: Extracts agency name, location, description, contact details (phone, email, website)
- 💾 **SQLite Database**: Stores data with automatic duplicate detection and schema initialization
- 📊 **CSV Export**: Export all agencies to CSV format for analysis
- 🔄 **Incremental Updates**: Skip already-scraped agencies to avoid re-scraping details
- 🏷️ **Active Status Tracking**: Automatically flags agencies as active/inactive based on website presence
- 📅 **Last Seen Tracking**: Records when each agency was last found on the website
- 🌐 **Anti-Bot Detection**: Includes user-agent rotation and browser simulation
- ⚡ **Async Operations**: Fast asynchronous web crawling using crawl4ai
- 🛡️ **Error Handling**: Robust retry logic and error management
- 🏗️ **Clean Architecture**: Modular code structure following OOP best practices

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/LuxembourgAgenciesExtractor.git
   cd LuxembourgAgenciesExtractor
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the scraper with:

```bash
python main.py
```

The scraper will:
1. Connect to (or create) a local SQLite database (`agencies.db`)
2. Scrape all pages from the Chambre Immobilière website
3. Extract agency information including descriptions from detail pages
4. Save new agencies to the database (skipping detail scraping for existing agencies)
5. Mark existing agencies as active and update their last_seen timestamp
6. Mark agencies not found during this run as inactive
7. Export results to `agencies.csv`

**Sample output:**
```
Starting Luxembourg Real Estate Agencies Scraper...
Total agencies in database: 150
Active agencies: 145

Scraping page 1...
Page 1: Found 20 agencies, saved 5 new, skipped 15 existing
...

Total agencies scraped: 148
Marked 2 agencies as inactive (no longer on website)

Database statistics:
  Total agencies: 153
  Active agencies: 148
  Inactive agencies: 5

Exported 153 agencies to agencies.csv
Done!
```

### Output Files

- **`agencies.db`**: SQLite database containing all scraped agencies with historical tracking
- **`agencies.csv`**: CSV export of all agencies with the following columns:
  - `unique_id`: Unique identifier for each agency
  - `name`: Agency name
  - `location`: Physical location/address
  - `description`: Agency description
  - `phone`: Contact phone number
  - `email`: Contact email address
  - `website`: Agency website URL
  - `detail_url`: URL to the agency's profile page
  - `is_active`: Whether the agency is currently listed on the website (True/False)

### Active/Inactive Status

The scraper automatically tracks which agencies are currently on the website:

- **Active** (`is_active=True`): Agency was found during the most recent scraping session
- **Inactive** (`is_active=False`): Agency exists in the database but was not found on the website

This allows you to:
- Track historical data for agencies that have closed or been delisted
- Identify when agencies disappear from the directory
- Maintain a complete historical record

When running the scraper multiple times:
- New agencies are added with active status
- Existing agencies found on the website have their `last_seen` timestamp updated
- Agencies not found during a scraping session are marked as inactive

## Project Structure

```
LuxembourgAgenciesExtractor/
├── src/
│   ├── __init__.py           # Package initialization
│   ├── models.py             # Agency data model
│   ├── database/             # Database module
│   │   ├── __init__.py       # Module exports
│   │   ├── manager.py        # Database operations (OOP)
│   │   └── queries.py        # SQL queries
│   └── scraper.py            # Web scraping logic
├── main.py                   # Entry point
├── requirements.txt          # Python dependencies
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

### Database Module

The database code is organized following OOP best practices:

- **`manager.py`**: Main `AgencyDatabase` class with:
  - Private methods for internal operations (prefixed with `_`)
  - Public API for database interactions
  - Comprehensive type hints and docstrings
  - Automatic schema initialization on first run
  
- **`queries.py`**: All SQL queries as module constants, separating SQL from business logic

## How It Works

1. **Web Crawling**: Uses `crawl4ai` with Playwright to navigate the website with JavaScript support
2. **HTML Parsing**: BeautifulSoup extracts structured data from HTML
3. **Data Modeling**: Dataclass-based `Agency` model with automatic unique ID generation
4. **Database Management**: 
   - SQLite stores agencies with duplicate prevention
   - Automatic database initialization on first run
   - Active/inactive status tracking
   - Last seen timestamp updates
5. **Rate Limiting**: Random delays between requests to respect server resources
6. **Incremental Scraping**: Only detail pages for new agencies are scraped; existing agencies just get timestamp updates

## Configuration

You can customize the scraper by modifying constants in [src/scraper.py](src/scraper.py):

- `BASE_URL`: The target URL pattern
- `USER_AGENTS`: List of user agents for rotation
- Delay intervals in `scrape_all_pages()` and `_enrich_agencies_with_details()`

## Dependencies

- **crawl4ai**: Modern async web crawler with JavaScript support
- **beautifulsoup4**: HTML parsing and data extraction

See [requirements.txt](requirements.txt) for specific versions.

## Legal & Ethical Considerations

⚠️ **Important**: This scraper is intended for educational and personal use only.

- Always respect the website's `robots.txt` file
- Be mindful of server load and use appropriate delays
- Do not use scraped data for commercial purposes without permission
- Ensure compliance with GDPR and other data protection regulations when handling personal information

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Troubleshooting

### Common Issues

**Browser installation error**:
If you encounter Playwright browser installation issues, run:
```bash
playwright install chromium
```

**Permission errors**:
Ensure you have write permissions in the project directory for database and CSV creation.

**Scraping failures**:
The website structure may change over time. Check the HTML selectors in [src/scraper.py](src/scraper.py) if scraping fails.

## Author

Ivan Donofrio

## Acknowledgments

- Data source: [Chambre Immobilière du Grand-Duché de Luxembourg](https://www.chambre-immobiliere.lu/)
- Built with [crawl4ai](https://github.com/unclecode/crawl4ai) and [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)

---

**Disclaimer**: This is an independent project and is not affiliated with or endorsed by the Chambre Immobilière du Grand-Duché de Luxembourg.
