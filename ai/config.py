"""
=============================================================================
Project : AI-Powered Retail Demand Forecasting &
          Inventory Optimization System

File : ai/config.py

Description :
Phase 8 - AI Decision Support settings. User-configurable values
(API key, model, tokens, temperature, timeout, word limit) stay in the
project's single central config.py per its own convention; this module
only re-exposes the ones the AI layer needs plus the fixed contract
(JSON schema keys, section labels) between the prompt, the model
response and the UI - those aren't deployment settings, they're part
of the code.
=============================================================================
"""

from config import (
    AI_MAX_RESPONSE_WORDS,
    AI_MAX_TOKENS,
    AI_MODEL,
    AI_REQUEST_TIMEOUT_SECONDS,
    AI_TEMPERATURE,
    GEMINI_API_KEY
)

__all__ = [
    "AI_MAX_RESPONSE_WORDS",
    "AI_MAX_TOKENS",
    "AI_MODEL",
    "AI_REQUEST_TIMEOUT_SECONDS",
    "AI_TEMPERATURE",
    "GEMINI_API_KEY",
    "INSIGHT_SECTIONS",
    "SECTION_LABELS",
    "NOT_AVAILABLE"
]

# Ordered JSON keys the model must return - the contract between
# prompt_builder (asks for these), the model response, and formatter
# (validates against these).
INSIGHT_SECTIONS = [
    "executive_summary",
    "business_recommendation",
    "inventory_action",
    "risk_explanation",
    "final_recommendation"
]

SECTION_LABELS = {

    "executive_summary": "Executive Summary",

    "business_recommendation": "Business Recommendation",

    "inventory_action": "Inventory Action",

    "risk_explanation": "Risk Explanation",

    "final_recommendation": "Final Recommendation"

}

# Shown to the model for fields the dataset doesn't provide, and
# reused for display so the UI and the prompt stay consistent.
NOT_AVAILABLE = "Not available"
