"""
Central configuration.

All knobs live here so scientists can experiment without touching
business logic. Override via environment variables or a .env file.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv("RACK_DATA_DIR", PROJECT_ROOT / "data"))
OUTPUT_DIR = Path(os.getenv("RACK_OUTPUT_DIR", PROJECT_ROOT / "output"))
EXTRACT_DIR = DATA_DIR / "extracted"

# ---------------------------------------------------------------------------
# Ollama / VLM
# ---------------------------------------------------------------------------
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
VLM_MODEL = os.getenv("VLM_MODEL", "qwen3-vl:4b")  # alternatives: gemma3:4b, llava, etc.
VLM_TIMEOUT = int(os.getenv("VLM_TIMEOUT", "300"))
VLM_MAX_RETRIES = int(os.getenv("VLM_MAX_RETRIES", "2"))

# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif", ".heic"}
DOC_EXT = {".pdf", ".docx", ".txt", ".md", ".rtf"}

# ---------------------------------------------------------------------------
# Schema keys the VLM is asked to produce
# ---------------------------------------------------------------------------
VLM_SCHEMA_KEYS = (
    "labels",
    "rack_units",
    "cables",
    "ports",
    "warnings",
    "procedures",
    "notes",
    "confidence",
)
