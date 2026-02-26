import asyncio
import logging
import sys

from src.scraper import AgencyScraper
from src.database import AgencyDatabase


def _setup_logger() -> logging.Logger:
    """Configure and return a logger that writes to stdout."""
    logger = logging.getLogger("main")
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


logger = _setup_logger()


async def main():
    """Main entry point for the Luxembourg agencies scraper."""
    logger.info("Starting Luxembourg Real Estate Agencies Scraper")

    db = AgencyDatabase()
    scraper = AgencyScraper(database=db)

    total_before = db.get_count()
    active_before = db.get_count(active_only=True)
    logger.info(
        f"Database before scraping: {total_before} total, {active_before} active"
    )

    # Scrape all current agencies from the website
    agencies = await scraper.scrape_all_pages()
    logger.info(f"Scraped {len(agencies)} agencies from website")

    # Mark agencies not found in this scraping session as inactive
    scraped_ids = {agency.unique_id for agency in agencies if agency.unique_id}
    inactive_count = db.mark_inactive_agencies(scraped_ids)

    if inactive_count > 0:
        logger.info(
            f"Marked {inactive_count} agencies as inactive (no longer on website)"
        )

    # Log final statistics
    total_after = db.get_count()
    active_after = db.get_count(active_only=True)
    inactive_after = total_after - active_after

    logger.info(
        f"Database after scraping: {total_after} total, {active_after} active, {inactive_after} inactive"
    )

    # Export all agencies (including inactive ones) to CSV
    db.export_to_csv()
    logger.info("Scraping session complete")


if __name__ == "__main__":
    asyncio.run(main())
