"""
Configuration for Reddit Sentiment Analysis System
"""
import os
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv

# Load environment variables from project-level .env file
BASE_DIR_PATH = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR_PATH.parent
load_dotenv(ROOT_DIR / ".env")

# Provider configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.1")

# LLM runtime controls
LLM_MAX_WORKERS = int(os.getenv("LLM_MAX_WORKERS", "2"))
LLM_REQUEST_DELAY = float(os.getenv("LLM_REQUEST_DELAY", "0.25"))
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

# Analysis Configuration
BATCH_SIZE = 10  # Process posts in batches to avoid rate limits
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Fields to analyze for sentiment
ANALYSIS_FIELDS = [
    "product_quality",      # How good/bad is Taboola as a product
    "user_experience",      # UX, ad quality, intrusiveness
    "business_practices",   # Ethics, transparency, partnerships
    "financial_performance",# Revenue, growth, investment potential
    "publisher_relations",  # How Taboola treats publishers
    "advertiser_value"      # Value proposition for advertisers
]

# Sentiment categories
SENTIMENT_CATEGORIES = ["positive", "neutral", "negative", "mixed"]

# Edge cases to handle
EDGE_CASES = {
    "sarcasm": "Detect and flag sarcastic comments",
    "mixed_sentiment": "Multiple sentiments in single text",
    "non_english": "Non-English content detection",
    "spam": "Bot or promotional content",
    "irrelevant": "Off-topic discussions"
}

# Output paths
BASE_DIR = str(BASE_DIR_PATH)
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
RESULTS_JSON = os.path.join(OUTPUT_DIR, "sentiment_results.json")
RESULTS_CSV = os.path.join(OUTPUT_DIR, "sentiment_summary.csv")
TRENDS_CSV = os.path.join(OUTPUT_DIR, "sentiment_trends.csv")
THEMES_JSON = os.path.join(OUTPUT_DIR, "top_themes.json")

# JSON Schema for LLM response
SENTIMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "overall_sentiment": {
            "type": "string",
            "enum": SENTIMENT_CATEGORIES
        },
        "field_sentiments": {
            "type": "object",
            "properties": {
                field: {
                    "type": "object",
                    "properties": {
                        "sentiment": {"type": "string", "enum": SENTIMENT_CATEGORIES},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "key_phrases": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["sentiment", "confidence"]
                }
                for field in ANALYSIS_FIELDS
            }
        },
        "edge_cases": {
            "type": "object",
            "properties": {
                "is_sarcastic": {"type": "boolean"},
                "has_mixed_sentiment": {"type": "boolean"},
                "is_non_english": {"type": "boolean"},
                "language": {"type": "string"},
                "is_spam": {"type": "boolean"}
            }
        },
        "themes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "theme": {"type": "string"},
                    "relevance": {"type": "number", "minimum": 0, "maximum": 1}
                }
            },
            "maxItems": 3
        },
        "reasoning": {"type": "string"}
    },
    "required": ["overall_sentiment", "field_sentiments", "edge_cases", "themes"]
}
FILTER_SCHEMA = {
    "type": "object",
    "properties": {
        "is_relevant": {"type": "boolean"},
        "mentions_taboola": {"type": "boolean"},
        "mentions_realize_product": {"type": "boolean"},
        "relevance_score": {"type": "number", "minimum": 0, "maximum": 10},
        "reasoning": {"type": "string"}
    },
    "required": ["is_relevant", "mentions_taboola", "relevance_score"]
}
DEFAULT_LLM_RESULT = {
    "is_relevant": False,
    "mentions_taboola": False,
    "mentions_realize_product": False,
    "relevance_score": 0.0,
    "raw_model_response": "",
}