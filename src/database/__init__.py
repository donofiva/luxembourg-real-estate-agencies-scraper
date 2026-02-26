"""
Database module for Luxembourg real estate agencies.

This module provides database management functionality with proper
separation of concerns between SQL queries and database operations.
"""

from .manager import AgencyDatabase

__all__ = ["AgencyDatabase"]
