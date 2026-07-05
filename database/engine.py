"""
=========================================================================
Database Engine Configuration
=========================================================================
"""

from sqlalchemy import create_engine

from config import DATABASE_PATH


DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True
)