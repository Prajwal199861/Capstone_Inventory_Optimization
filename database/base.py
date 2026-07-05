"""
=========================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : base.py

Description :
Defines the SQLAlchemy Declarative Base class that all ORM models
will inherit from.
=========================================================================
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all database models.
    """
    pass