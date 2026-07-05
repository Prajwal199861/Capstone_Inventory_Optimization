"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : base_repository.py

Description :
Base repository providing common database session handling.
=============================================================================
"""

from database.session import SessionLocal


class BaseRepository:

    def __init__(self):

        self.session = SessionLocal()

    def commit(self):

        self.session.commit()

    def rollback(self):

        self.session.rollback()

    def close(self):

        self.session.close()