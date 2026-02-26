"""Web scraper for Luxembourg real estate agencies from Chambre Immobilière."""

import asyncio
import logging
import random
import sys
from typing import List, Optional, Set, TYPE_CHECKING, Any

from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

from .models import Agency

if TYPE_CHECKING:
    from .database import AgencyDatabase


# ============================================================================
# Logging Configuration
# ============================================================================


def _setup_logger(name: str) -> logging.Logger:
    """Configure and return a logger that writes to stdout."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


logger = _setup_logger(__name__)


# ============================================================================
# Constants
# ============================================================================

BASE_URL = "https://www.chambre-immobiliere.lu/page/{}/?_sort&s&post_type=hp_listing&latitude&longitude&_category=68&location&ville_entreprise&cp_entreprise&adresse_entreprise&email_contact&telephone&website"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
]

ANTI_BOT_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
window.chrome = {runtime: {}};
Object.defineProperty(navigator, 'permissions', {
    get: () => ({
        query: () => Promise.resolve({state: 'granted'})
    })
});
"""

# Retry and timing configuration
MAX_PAGE_RETRIES = 3
MAX_DETAIL_RETRIES = 2
PAGE_TIMEOUT_MS = 30000
DETAIL_TIMEOUT_MS = 30000
PAGE_DELAY_RANGE = (3.0, 6.0)
DETAIL_DELAY_RANGE = (1.5, 3.5)
RETRY_DELAY_RANGE = (5.0, 10.0)


# ============================================================================
# Helper Classes
# ============================================================================


class HTMLExtractor:
    """Helper class for extracting data from HTML."""

    @staticmethod
    def extract_basic_info(listing) -> Optional[Agency]:
        """
        Extract basic agency info from a listing card.

        Args:
            listing: BeautifulSoup element containing a listing

        Returns:
            Agency object or None if extraction fails
        """
        title_elem = listing.find("h4", class_="hp-listing__title")
        if not title_elem:
            return None

        name = title_elem.get_text(strip=True)
        detail_url = None
        title_link = title_elem.find("a")
        if title_link and title_link.get("href"):
            detail_url = title_link["href"]

        location = None
        location_elem = listing.find(class_="hp-listing__location")
        if location_elem:
            location = location_elem.get_text(strip=True)

        footer = listing.find("footer")
        phone = HTMLExtractor._extract_contact_attribute(footer, "telephone")
        email = HTMLExtractor._extract_contact_attribute(footer, "email-contact")
        website = HTMLExtractor._extract_contact_attribute(footer, "website")

        return Agency(
            name=name,
            location=location,
            phone=phone,
            email=email,
            website=website,
            detail_url=detail_url,
        )

    @staticmethod
    def extract_description(html: str) -> Optional[str]:
        """
        Extract description from agency detail page.

        Args:
            html: HTML content of the detail page

        Returns:
            Description text or None
        """
        soup = BeautifulSoup(html, "html.parser")
        desc_elem = soup.find(class_="hp-listing__description")
        return desc_elem.get_text(strip=True) if desc_elem else None

    @staticmethod
    def _extract_contact_attribute(footer, attr_type: str) -> Optional[str]:
        """
        Extract contact attribute from footer.

        Args:
            footer: BeautifulSoup element containing footer
            attr_type: Type of attribute to extract (telephone, email-contact, website)

        Returns:
            Extracted attribute value or None
        """
        if not footer:
            return None

        attr_elem = footer.find(class_=f"hp-listing__attribute--{attr_type}")
        if not attr_elem:
            return None

        link = attr_elem.find("a")
        if link:
            href = link.get("href", "")
            if attr_type == "email-contact" and href.startswith("mailto:"):
                return href.replace("mailto:", "")
            elif attr_type == "telephone" and href.startswith("tel:"):
                return href.replace("tel:", "")
            elif attr_type == "website":
                return href
            return link.get_text(strip=True)

        return attr_elem.get_text(strip=True)


class BrowserConfigBuilder:
    """Builder for browser configuration."""

    @staticmethod
    def build() -> BrowserConfig:
        """
        Create optimized browser configuration.

        Returns:
            Configured BrowserConfig instance
        """
        return BrowserConfig(
            headless=True,
            verbose=False,
            extra_args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-infobars",
                "--window-position=0,0",
                "--ignore-certificate-errors",
                "--ignore-certificate-errors-spki-list",
                "--disable-accelerated-2d-canvas",
                "--disable-gpu",
            ],
            user_agent=random.choice(USER_AGENTS),
            viewport_width=random.randint(1366, 1920),
            viewport_height=random.randint(768, 1080),
            accept_downloads=False,
            java_script_enabled=True,
        )


# ============================================================================
# Main Scraper Class
# ============================================================================


class AgencyScraper:
    """
    Web scraper for Luxembourg real estate agencies from Chambre Immobilière.

    Handles scraping agency listings and detail pages with proper error handling,
    rate limiting, and database integration.
    """

    def __init__(self, database: Optional["AgencyDatabase"] = None):
        """
        Initialize the scraper.

        Args:
            database: Optional AgencyDatabase instance for storing results
        """
        self._agencies: List[Agency] = []
        self._database = database
        self._existing_ids: Set[str] = set()

        if self._database:
            self._existing_ids = self._database.get_existing_ids()

    async def scrape_all_pages(self) -> List[Agency]:
        """
        Scrape all pages and extract agency data.

        Returns:
            List of Agency objects
        """
        logger.info("Starting scraping session")

        browser_config = BrowserConfigBuilder.build()

        async with AsyncWebCrawler(config=browser_config) as crawler:
            page_num = 1
            while True:
                agencies_on_page = await self._scrape_page_safely(crawler, page_num)

                if not agencies_on_page:
                    logger.info("Scraping complete")
                    break

                await self._enrich_agencies_with_details(crawler, agencies_on_page)
                self._agencies.extend(agencies_on_page)

                if self._database:
                    await self._save_agencies_to_database(agencies_on_page, page_num)

                await self._wait_before_next_request()
                page_num += 1

        logger.info(f"Scraping session complete. Total: {len(self._agencies)} agencies")
        return self._agencies

    async def _scrape_page_safely(
        self, crawler: AsyncWebCrawler, page_num: int
    ) -> List[Agency]:
        """
        Scrape a single page with retry logic.

        Args:
            crawler: AsyncWebCrawler instance
            page_num: Page number to scrape

        Returns:
            List of agencies found on the page
        """
        for attempt in range(MAX_PAGE_RETRIES):
            try:
                logger.info(
                    f"Scraping page {page_num} (attempt {attempt + 1}/{MAX_PAGE_RETRIES})"
                )
                agencies = await self._scrape_page(crawler, page_num)
                return agencies
            except Exception as e:
                logger.warning(f"Page {page_num} failed: {str(e)[:100]}")

                if attempt < MAX_PAGE_RETRIES - 1:
                    await self._wait_before_retry()
                else:
                    logger.error(
                        f"Failed to scrape page {page_num} after {MAX_PAGE_RETRIES} attempts"
                    )
                    return []

        return []

    async def _scrape_page(
        self, crawler: AsyncWebCrawler, page_num: int
    ) -> List[Agency]:
        """
        Scrape a single page and extract basic agency info.

        Args:
            crawler: AsyncWebCrawler instance
            page_num: Page number to scrape

        Returns:
            List of agencies found on the page

        Raises:
            RuntimeError: If the page fetch fails
        """
        url = BASE_URL.format(page_num)

        crawl_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            wait_for="css:.hp-listing",
            page_timeout=PAGE_TIMEOUT_MS,
            magic=True,
            simulate_user=True,
            override_navigator=True,
            delay_before_return_html=2.0,
            js_code=ANTI_BOT_JS,
        )

        result = await crawler.arun(url=url, config=crawl_config)  # type: ignore

        if not result.success:  # type: ignore
            raise RuntimeError(f"Failed to fetch page {page_num}")

        soup = BeautifulSoup(result.html, "html.parser")  # type: ignore
        listings = soup.find_all(class_="hp-listing")

        if not listings:
            return []

        agencies = []
        for listing in listings:
            agency = HTMLExtractor.extract_basic_info(listing)
            if agency:
                agencies.append(agency)

        logger.info(f"Found {len(agencies)} agencies on page {page_num}")
        return agencies

    async def _enrich_agencies_with_details(
        self, crawler: AsyncWebCrawler, agencies: List[Agency]
    ) -> None:
        """
        Fetch detail pages for new agencies and extract descriptions.

        Args:
            crawler: AsyncWebCrawler instance
            agencies: List of agencies to enrich
        """
        new_agencies = [
            agency
            for agency in agencies
            if agency.unique_id and agency.unique_id not in self._existing_ids
        ]

        if not new_agencies:
            logger.info(f"All {len(agencies)} agencies already in database")
            return

        logger.info(f"Fetching details for {len(new_agencies)} new agencies")

        for agency in new_agencies:
            if not agency.detail_url:
                continue

            await self._scrape_agency_detail_safely(crawler, agency)
            await self._wait_before_next_request()

    async def _scrape_agency_detail_safely(
        self, crawler: AsyncWebCrawler, agency: Agency
    ) -> None:
        """
        Scrape agency detail page with retry logic.

        Args:
            crawler: AsyncWebCrawler instance
            agency: Agency to enrich
        """
        for attempt in range(MAX_DETAIL_RETRIES):
            try:
                logger.debug(
                    f"Fetching details for: {agency.name} (attempt {attempt + 1}/{MAX_DETAIL_RETRIES})"
                )
                await self._scrape_agency_detail(crawler, agency)
                return
            except Exception as e:
                logger.warning(f"Detail fetch failed for {agency.name}: {str(e)[:100]}")

                if attempt < MAX_DETAIL_RETRIES - 1:
                    await self._wait_before_retry()
                else:
                    logger.warning(
                        f"Could not fetch details for {agency.name} after {MAX_DETAIL_RETRIES} attempts"
                    )

    async def _scrape_agency_detail(
        self, crawler: AsyncWebCrawler, agency: Agency
    ) -> None:
        """
        Scrape agency detail page for description.

        Args:
            crawler: AsyncWebCrawler instance
            agency: Agency to scrape details for

        Raises:
            RuntimeError: If the detail page fetch fails
        """
        if not agency.detail_url:
            raise RuntimeError(f"Agency {agency.name} has no detail URL")

        crawl_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            wait_for="css:body",
            page_timeout=DETAIL_TIMEOUT_MS,
            magic=True,
            simulate_user=True,
            override_navigator=True,
            delay_before_return_html=1.5,
            js_code=ANTI_BOT_JS,
        )

        result = await crawler.arun(url=agency.detail_url, config=crawl_config)  # type: ignore

        if not result.success:  # type: ignore
            raise RuntimeError(f"Failed to fetch detail page for {agency.name}")

        description = HTMLExtractor.extract_description(result.html)  # type: ignore
        if description:
            agency.description = description

    async def _save_agencies_to_database(
        self, agencies: List[Agency], page_num: int
    ) -> None:
        """
        Save agencies to database and update tracking.

        Args:
            agencies: List of agencies to save
            page_num: Current page number (for logging)
        """
        if not self._database:
            return

        new_count, updated_count, skipped_count = self._database.save_agencies(agencies)

        logger.info(
            f"Page {page_num}: {len(agencies)} found, "
            f"{new_count} new, {updated_count} updated"
        )

        self._existing_ids.update(
            agency.unique_id for agency in agencies if agency.unique_id
        )

    @staticmethod
    async def _wait_before_next_request() -> None:
        """Wait before making the next request to be respectful to the server."""
        delay = random.uniform(*PAGE_DELAY_RANGE)
        await asyncio.sleep(delay)

    @staticmethod
    async def _wait_before_retry() -> None:
        """Wait before retrying a failed request."""
        delay = random.uniform(*RETRY_DELAY_RANGE)
        logger.debug(f"Waiting {delay:.1f}s before retry...")
        await asyncio.sleep(delay)
