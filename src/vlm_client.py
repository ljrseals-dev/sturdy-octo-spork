"""
Local vision-language model client (Ollama).

Why this design
---------------
1. We never send images off the machine.
2. The system prompt is treated as a scientific instrument: it is versioned,
   configurable, and produces a fixed schema so downstream code can be typed.
3. Retries + latency measurement give us observability that pure research
   scripts usually lack.
"""

from __future__ import annotations

import base64
import json
import logging
import time
from typing import Any

import requests

from .config import OLLAMA_URL, VLM_MAX_RETRIES, VLM_MODEL, VLM_SCHEMA_KEYS, VLM_TIMEOUT
from .schemas import VLMAnalysis

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = f"""You are an expert at reading server-room photographs and technical documents.
Your only job is to extract structured facts that a human technician or auditor would care about.

Return STRICT JSON with exactly these keys:
{json.dumps(list(VLM_SCHEMA_KEYS))}

Rules:
- lists contain short strings only
- confidence is a float 0.0–1.0 reflecting how sure you are of the extraction
- if something is not visible, return an empty list (do not invent)
- never add extra keys
"""


def _b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _call_ollama(path: str, prompt: str | None = None) -> dict[str, Any]:
    payload = {
        "model": VLM_MODEL,
        "prompt": prompt or SYSTEM_PROMPT,
        "images": [_b64(path)],
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.1,  # low temperature for factual extraction
        },
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=VLM_TIMEOUT)
    r.raise_for_status()
    return r.json()


def analyze_image(path: str, prompt: str | None = None) -> tuple[VLMAnalysis, int]:
    """
    Analyse a single image and return (structured result, latency_ms).

    Raises on permanent failure after retries.
    """
    last_err: Exception | None = None
    for attempt in range(1, VLM_MAX_RETRIES + 2):
        t0 = time.perf_counter()
        try:
            raw = _call_ollama(path, prompt)
            latency_ms = int((time.perf_counter() - t0) * 1000)
            text = raw.get("response", "")
            data = json.loads(text)
            analysis = VLMAnalysis.model_validate(data)
            logger.debug("VLM success on %s (attempt %d, %d ms)", path, attempt, latency_ms)
            return analysis, latency_ms
        except Exception as e:
            last_err = e
            logger.warning("VLM attempt %d failed for %s: %s", attempt, path, e)
            if attempt <= VLM_MAX_RETRIES:
                time.sleep(1.5 * attempt)
    raise RuntimeError(f"VLM failed after retries: {last_err}") from last_err
