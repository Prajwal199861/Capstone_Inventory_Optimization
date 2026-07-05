"""
=========================================================================
Database Initialization
=========================================================================
"""

from .base import Base
from .engine import engine


def initialize_database():
    """
    Create all database tables.
    """

    Base.metadata.create_all(bind=engine)