"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : session.py

Description :
Creates database sessions.

Every database operation should obtain a session from this file.
=============================================================================
"""

from sqlalchemy.orm import sessionmaker

from .engine import engine


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True
)


def get_session():
    """
    Returns a new SQLAlchemy database session.

    Usage:

        with get_session() as session:
            ...
    """

    return SessionLocal()