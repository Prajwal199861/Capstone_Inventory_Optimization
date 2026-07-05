"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

Repository : Capstone_Inventory_Optimization

File : base.py

Author : Group -2

Version : 0.1.0

Description :
Defines the SQLAlchemy Declarative Base class.

All ORM models (User, Role, Product, Sales, Inventory, etc.)
must inherit from this class.

=============================================================================
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.

    SQLAlchemy uses this class to maintain metadata about all tables
    defined in the application.

    Every database model should inherit from this class.

    Example:
        class User(Base):
            __tablename__ = "users"
    """

    pass