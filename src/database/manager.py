"""Database manager for real estate agencies with proper OOP design."""

import csv
import logging
import sqlite3
from typing import List, Set, Optional, Tuple
from pathlib import Path

from ..models import Agency
from . import queries

logger = logging.getLogger(__name__)


class AgencyDatabase:
    """
    SQLite database manager for real estate agencies.

    Manages database connections, migrations, and CRUD operations
    for agency records following OOP best practices.
    """

    def __init__(self, db_path: str = "agencies.db"):
        """
        Initialize database manager.

        Args:
            db_path: Path to the SQLite database file
        """
        self._db_path = db_path
        self._init_database()
        self._run_migrations()

    @property
    def db_path(self) -> str:
        """Get database path."""
        return self._db_path

    def _get_connection(self) -> sqlite3.Connection:
        """
        Create and return a database connection.

        Returns:
            SQLite connection object
        """
        return sqlite3.connect(self._db_path)

    def _init_database(self) -> None:
        """Initialize database and create table if not exists."""
        with self._get_connection() as conn:
            conn.execute(queries.CREATE_TABLE_QUERY)
            conn.commit()

    def _column_exists(self, column_name: str) -> bool:
        """
        Check if a column exists in the agencies table.

        Args:
            column_name: Name of the column to check

        Returns:
            True if column exists, False otherwise
        """
        with self._get_connection() as conn:
            cursor = conn.execute(queries.SELECT_COLUMN_EXISTS, (column_name,))
            return cursor.fetchone()[0] > 0

    def _run_migrations(self) -> None:
        """Run database migrations to add new columns if needed."""
        with self._get_connection() as conn:
            try:
                # Add is_active column if it doesn't exist
                if not self._column_exists("is_active"):
                    conn.execute(queries.ADD_IS_ACTIVE_COLUMN)
                    conn.commit()

                # Add last_seen_at column if it doesn't exist
                if not self._column_exists("last_seen_at"):
                    conn.execute(queries.ADD_LAST_SEEN_COLUMN)
                    # Set initial values for existing records
                    conn.execute(queries.UPDATE_LAST_SEEN_FOR_EXISTING)
                    conn.commit()
            except sqlite3.OperationalError as e:
                # Column might already exist
                pass

    def get_existing_ids(self, active_only: bool = False) -> Set[str]:
        """
        Get all existing agency unique IDs.

        Args:
            active_only: If True, only return IDs of active agencies

        Returns:
            Set of unique IDs
        """
        query = (
            queries.SELECT_ACTIVE_UNIQUE_IDS
            if active_only
            else queries.SELECT_ALL_UNIQUE_IDS
        )

        with self._get_connection() as conn:
            cursor = conn.execute(query)
            return {row[0] for row in cursor.fetchall()}

    def save_agencies(self, agencies: List[Agency]) -> Tuple[int, int, int]:
        """
        Save agencies to database.

        For existing agencies, marks them as active and updates their
        last_seen_at timestamp. For new agencies, inserts them.
        This does NOT update other fields for existing agencies.

        Args:
            agencies: List of Agency objects to save

        Returns:
            Tuple of (new_count, updated_count, skipped_count)
        """
        existing_ids = self.get_existing_ids()
        new_count = 0
        updated_count = 0
        skipped_count = 0

        with self._get_connection() as conn:
            for agency in agencies:
                if agency.unique_id in existing_ids:
                    # Mark as active and update last_seen_at timestamp
                    # Does NOT update other agency fields
                    conn.execute(
                        queries.REACTIVATE_AND_UPDATE_LAST_SEEN, (agency.unique_id,)
                    )
                    updated_count += 1
                else:
                    # Insert new agency
                    self._insert_agency(conn, agency)
                    new_count += 1

            conn.commit()

        return new_count, updated_count, skipped_count

    def _insert_agency(self, conn: sqlite3.Connection, agency: Agency) -> None:
        """
        Insert a single agency into the database.

        Args:
            conn: Database connection
            agency: Agency object to insert
        """
        conn.execute(
            queries.INSERT_AGENCY,
            (
                agency.unique_id,
                agency.name,
                agency.location,
                agency.description,
                agency.phone,
                agency.email,
                agency.website,
                agency.detail_url,
                1 if agency.is_active else 0,
            ),
        )

    def mark_inactive_agencies(self, active_ids: Set[str]) -> int:
        """
        Mark agencies as inactive if they're not in the provided set of active IDs.

        This is used to flag agencies that disappeared from the website
        during a scraping session.

        Args:
            active_ids: Set of unique IDs for agencies that are currently active

        Returns:
            Number of agencies marked as inactive
        """
        if not active_ids:
            return 0

        placeholders = ",".join("?" * len(active_ids))
        query = queries.MARK_AGENCIES_INACTIVE.format(placeholders=placeholders)

        with self._get_connection() as conn:
            cursor = conn.execute(query, tuple(active_ids))
            conn.commit()
            return cursor.rowcount

    def export_to_csv(
        self, csv_path: str = "agencies.csv", active_only: bool = False
    ) -> None:
        """
        Export agencies to CSV file.

        Args:
            csv_path: Path to the output CSV file
            active_only: If True, only export active agencies
        """
        query = (
            queries.SELECT_ACTIVE_AGENCIES
            if active_only
            else queries.SELECT_ALL_AGENCIES
        )

        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query)
            rows = cursor.fetchall()

            if not rows:
                logger.warning("No agencies to export")
                return

            self._write_csv(csv_path, rows)

    def _write_csv(self, csv_path: str, rows: List[sqlite3.Row]) -> None:
        """
        Write rows to CSV file.

        Args:
            csv_path: Path to the output CSV file
            rows: List of database rows to write
        """
        fieldnames = [
            "unique_id",
            "name",
            "location",
            "description",
            "phone",
            "email",
            "website",
            "detail_url",
            "is_active",
        ]

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for row in rows:
                row_dict = dict(row)
                # Convert is_active from 0/1 to False/True for better readability
                row_dict["is_active"] = bool(row_dict["is_active"])
                writer.writerow(row_dict)

        logger.info(f"Exported {len(rows)} agencies to {csv_path}")

    def get_count(self, active_only: bool = False) -> int:
        """
        Get total number of agencies in database.

        Args:
            active_only: If True, only count active agencies

        Returns:
            Number of agencies
        """
        query = queries.SELECT_ACTIVE_COUNT if active_only else queries.SELECT_COUNT

        with self._get_connection() as conn:
            cursor = conn.execute(query)
            return cursor.fetchone()[0]
