"""
OCR stage (currently a clean stub).

Scientific note
---------------
Two strong offline candidates in 2025–2026:
  • Xiaomi-OCR-0  – high accuracy on technical drawings and low-quality scans
  • MinerU 2.5-Pro – layout-aware PDF understanding

The interface below is deliberately narrow so either model (or a future
one) can be dropped in without changing the pipeline contract.
"""

from __future__ import annotations

import logging
from pathlib import Path

from .schemas import DocResult

logger = logging.getLogger(__name__)


def extract_text(path: str | Path) -> DocResult:
    """
    Extract text + light structure from a document.

    Today this is a stub that marks the file as pending_ocr.
    Replace the body with a real local OCR call.
    """
    p = Path(path)
    logger.info("OCR stub called for %s", p.name)

    # ------------------------------------------------------------------
    # Future scientists: replace this block
    # ------------------------------------------------------------------
    # Example sketch for a real backend:
    #
    # from your_ocr_lib import run_ocr
    # pages = run_ocr(str(p))
    # full_text = "\n\n".join(page["text"] for page in pages)
    # return DocResult(
    #     file=str(p),
    #     status="ok",
    #     text=full_text,
    #     pages=pages,
    # )
    # ------------------------------------------------------------------

    return DocResult(
        file=str(p.resolve()),
        status="pending_ocr",
        text=None,
        pages=[],
        notes=(
            "Stub. Wire Xiaomi-OCR-0 or MinerU2.5-Pro here. "
            "Keep the same DocResult shape so the rest of the pipeline stays unchanged."
        ),
    )
