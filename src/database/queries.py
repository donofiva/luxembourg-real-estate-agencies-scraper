"""SQL queries for agency database operations."""

# Table Creation
CREATE_TABLE_QUERY = """
    CREATE TABLE IF NOT EXISTS agencies (
        unique_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        location TEXT,
        description TEXT,
        phone TEXT,
        email TEXT,
        website TEXT,
        detail_url TEXT,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
"""

# Migration query to add new columns to existing tables
ADD_IS_ACTIVE_COLUMN = """
    ALTER TABLE agencies 
    ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1
"""

ADD_LAST_SEEN_COLUMN = """
    ALTER TABLE agencies 
    ADD COLUMN last_seen_at TIMESTAMP
"""

# Update query to set last_seen_at for existing records
UPDATE_LAST_SEEN_FOR_EXISTING = """
    UPDATE agencies 
    SET last_seen_at = created_at 
    WHERE last_seen_at IS NULL
"""

# Select Queries
SELECT_ALL_UNIQUE_IDS = "SELECT unique_id FROM agencies"

SELECT_ACTIVE_UNIQUE_IDS = "SELECT unique_id FROM agencies WHERE is_active = 1"

SELECT_COUNT = "SELECT COUNT(*) FROM agencies"

SELECT_ACTIVE_COUNT = "SELECT COUNT(*) FROM agencies WHERE is_active = 1"

SELECT_ALL_AGENCIES = """
    SELECT unique_id, name, location, description, phone, email, website, detail_url, is_active
    FROM agencies
    ORDER BY name
"""

SELECT_ACTIVE_AGENCIES = """
    SELECT unique_id, name, location, description, phone, email, website, detail_url, is_active
    FROM agencies
    WHERE is_active = 1
    ORDER BY name
"""

SELECT_COLUMN_EXISTS = """
    SELECT COUNT(*) 
    FROM pragma_table_info('agencies') 
    WHERE name = ?
"""

# Insert/Update Queries
INSERT_AGENCY = """
    INSERT INTO agencies 
    (unique_id, name, location, description, phone, email, website, detail_url, is_active, last_seen_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
"""

UPDATE_AGENCY_STATUS = """
    UPDATE agencies 
    SET is_active = ?, last_seen_at = CURRENT_TIMESTAMP
    WHERE unique_id = ?
"""

UPDATE_LAST_SEEN = """
    UPDATE agencies 
    SET last_seen_at = CURRENT_TIMESTAMP
    WHERE unique_id = ?
"""

REACTIVATE_AND_UPDATE_LAST_SEEN = """
    UPDATE agencies 
    SET is_active = 1, last_seen_at = CURRENT_TIMESTAMP
    WHERE unique_id = ?
"""

MARK_AGENCIES_INACTIVE = """
    UPDATE agencies 
    SET is_active = 0
    WHERE unique_id NOT IN ({placeholders})
    AND is_active = 1
"""
