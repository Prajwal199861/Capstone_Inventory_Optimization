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

import os
from pathlib import Path

from dotenv import load_dotenv

# Loads .env (gitignored) into the process environment if present; a
# deployment without a .env file just falls back to real env vars.
load_dotenv()


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
# Inventory Optimization Configuration (Milestone 3 - Phase 3)
# =============================================================================

# Days between placing a replenishment order and receiving it. Used
# whenever the dataset carries no per-product lead time.
DEFAULT_LEAD_TIME_DAYS = 7

# How often stock is reviewed and orders are placed. An order must
# cover demand until the NEXT review plus the lead time.
DEFAULT_REVIEW_PERIOD_DAYS = 7

# Probability of not stocking out during the lead time.
DEFAULT_SERVICE_LEVEL = 0.95

# Normal distribution z-scores for the supported service levels.
SERVICE_LEVEL_Z_SCORES = {

    0.80: 0.84,

    0.90: 1.28,

    0.95: 1.65,

    0.98: 2.05,

    0.99: 2.33

}

# Fallback safety buffer (in days of average demand) used when demand
# variability cannot be measured from the forecast.
DEFAULT_SAFETY_STOCK_DAYS = 3

# Stock above this multiple of the forecast demand over the horizon is
# flagged as overstock.
DEFAULT_OVERSTOCK_FACTOR = 2.0

# Reorder quantities are rounded up to a multiple of this value
# (e.g. case/pallet sizes).
DEFAULT_ORDER_MULTIPLE = 1

DEFAULT_MINIMUM_ORDER_QUANTITY = 0


# =============================================================================
# AI Decision Support Configuration (Phase 8)
# =============================================================================

# Read from the environment (.env locally, real env vars in
# deployment) - never hardcode a key here.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

AI_MODEL = os.getenv("AI_MODEL", "gemini-2.5-flash")

AI_MAX_TOKENS = 900

AI_TEMPERATURE = 0.3

AI_REQUEST_TIMEOUT_SECONDS = 30

# Prompt guideline from the handover doc: keep insights skimmable.
AI_MAX_RESPONSE_WORDS = 250


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
