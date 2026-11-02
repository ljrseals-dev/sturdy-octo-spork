"""
Pydantic models that define the contract between the models and the rest
of the system. Scientists can evolve these schemas without touching the
I/O or orchestration layers.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class VLMAnalysis(BaseModel):
    """Structured output expected from the vision-language model."""

    labels: list[str] = Field(default_factory=list, description="Visible text labels, asset tags, serials")
    rack_units: list[str] = Field(default_factory=list, description="RU numbers or height markers")
    cables: list[str] = Field(default_factory=list, description="Cable types / colours / connectors observed")
    ports: list[str] = Field(default_factory=list, description="Port numbers, patch-panel identifiers")
    warnings: list[str] = Field(default_factory=list, description="Warning stickers, safety notices")
    procedures: list[str] = Field(default_factory=list, description="Any written operating steps")
    notes: str = Field(default="", description="Free-form observations")
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Model self-reported confidence")


class ImageResult(BaseModel):
    file: str
    analysis: Optional[VLMAnalysis] = None
    error: Optional[str] = None
    model: Optional[str] = None
    latency_ms: Optional[int] = None


class DocResult(BaseModel):
    file: str
    status: str = "pending_ocr"
    text: Optional[str] = None
    pages: list[dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None
    notes: Optional[str] = None


class PipelineResult(BaseModel):
    source_zip: str
    images: list[ImageResult] = Field(default_factory=list)
    docs: list[DocResult] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)
