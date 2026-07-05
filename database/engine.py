"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : engine.py

Description :
Creates and configures the SQLAlchemy Engine.

The engine is responsible for establishing the connection
between the application and the database.
=============================================================================
"""

from sqlalchemy import create_engine

import config


DATABASE_URL = f"sqlite:///{config.DATABASE_PATH}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True
)