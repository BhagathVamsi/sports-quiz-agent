"""
config.py
---------
Centralized configuration. Loads secrets from a local .env file so API keys
are never hardcoded or committed to source control.

Supports THREE interchangeable LLM providers:
  - "openai"    -> uses OPENAI_API_KEY (gpt-4o / gpt-3.5-turbo)
  - "anthropic" -> uses ANTHROPIC_API_KEY (claude-sonnet models)
  - "gemini"    -> uses GEMINI_API_KEY (gemini-2.5-flash) -- has a genuine
                    free tier (no credit card) so this is the easiest one
                    to get running with zero cost.

Switch providers by setting LLM_PROVIDER in your .env file.
"""

import os
from dotenv import load_dotenv

# Load variables from .env file into the environment
load_dotenv()

# Which LLM backend to use: "openai", "anthropic", or "gemini"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai").strip().lower()

# Provider credentials
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Model names (override in .env if you want a different model)
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ChromaDB storage location and collection name
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
CHROMA_COLLECTION_NAME = "sports_history"

# Path to the offline facts file used to seed ChromaDB
SPORTS_FACTS_PATH = os.getenv("SPORTS_FACTS_PATH", "./data/sports_facts.json")


def validate_config():
    """Raises a clear error early if required keys are missing, instead of
    failing deep inside an API call later."""
    if LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
        raise EnvironmentError(
            "LLM_PROVIDER is 'openai' but OPENAI_API_KEY is missing from your .env file."
        )
    if LLM_PROVIDER == "anthropic" and not ANTHROPIC_API_KEY:
        raise EnvironmentError(
            "LLM_PROVIDER is 'anthropic' but ANTHROPIC_API_KEY is missing from your .env file."
        )
    if LLM_PROVIDER == "gemini" and not GEMINI_API_KEY:
        raise EnvironmentError(
            "LLM_PROVIDER is 'gemini' but GEMINI_API_KEY is missing from your .env file."
        )
    if LLM_PROVIDER not in ("openai", "anthropic", "gemini"):
        raise EnvironmentError(
            f"Unknown LLM_PROVIDER '{LLM_PROVIDER}'. Use 'openai', 'anthropic', or 'gemini'."
        )
