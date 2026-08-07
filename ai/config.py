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
    "EXECUTIVE_SECTIONS",
    "EXECUTIVE_SECTION_LABELS",
    "EXECUTIVE_MAX_RESPONSE_WORDS",
    "NOT_AVAILABLE"
]

# Ordered JSON keys the model must return - the contract between
# prompt_builder (asks for these), the model response, and formatter
# (validates against these). Per-product AI Insight (Phase 8).
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

# Same contract, for the dataset-wide AI Executive Report (Milestone
# 4 - Phase 3). A different schema, so ai_service.generate() takes
# `sections` as a parameter rather than hardcoding one shape - the
# API-call layer itself is unchanged.
EXECUTIVE_SECTIONS = [
    "overall_health",
    "critical_issues",
    "positive_findings",
    "immediate_actions",
    "management_recommendations"
]

EXECUTIVE_SECTION_LABELS = {

    "overall_health": "Overall Inventory Health",

    "critical_issues": "Critical Issues",

    "positive_findings": "Positive Findings",

    "immediate_actions": "Immediate Actions",

    "management_recommendations": "Management Recommendations"

}

# A dataset-wide summary covers more ground than one product, so it
# gets a slightly larger word budget than the per-product insight.
EXECUTIVE_MAX_RESPONSE_WORDS = 400

# Shown to the model for fields the dataset doesn't provide, and
# reused for display so the UI and the prompt stay consistent.
NOT_AVAILABLE = "Not available"
