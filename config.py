"""
=========================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

Repository : Capstone_Inventory_Optimization

File : config.py

Author : Capstone Group -2 

Version : 0.1.0

Description :
Central configuration file for the application.
All configurable values should be defined here instead of hardcoding
them throughout the project.
=========================================================================
"""

from pathlib import Path


# =============================================================================
# Project Information
# =============================================================================

APP_NAME = "AI-Powered Retail Demand Forecasting & Inventory Optimization"

APP_SHORT_NAME = "Retail Demand AI"

VERSION = "0.1.0"

AUTHOR = "Capstone Group -2 "


# =============================================================================
# Project Directories
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent

ASSETS_DIR = BASE_DIR / "assets"

DATABASE_DIR = BASE_DIR / "database"

UPLOADS_DIR = BASE_DIR / "uploads"

EXPORTS_DIR = BASE_DIR / "exports"

LOGS_DIR = BASE_DIR / "logs"

DATASETS_DIR = BASE_DIR / "datasets"

DOCS_DIR = BASE_DIR / "docs"


# =============================================================================
# Database
# =============================================================================

# =============================================================================
# Database Configuration
# =============================================================================

DATABASE_ENGINE = "sqlite"

DATABASE_NAME = "retail_inventory.db"

DATABASE_PATH = DATABASE_DIR / DATABASE_NAME

# =============================================================================
# File Upload Configuration
# =============================================================================

ALLOWED_FILE_TYPES = [
    "csv",
    "xlsx",
    "xls"
]

MAX_UPLOAD_SIZE_MB = 100


# =============================================================================
# Forecast Configuration
# =============================================================================

DEFAULT_FORECAST_MONTHS = 3


# =============================================================================
# Logging
# =============================================================================

LOG_LEVEL = "INFO"

LOG_FILE = LOGS_DIR / "application.log"


# =============================================================================
# Authentication
# =============================================================================

SESSION_TIMEOUT_MINUTES = 30


# =============================================================================
# Theme
# =============================================================================

PRIMARY_COLOR = "#1565C0"

SECONDARY_COLOR = "#26A69A"
