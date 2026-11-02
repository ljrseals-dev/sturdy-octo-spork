"""
End-to-end orchestration.

This is the single entry-point a scientist or operator runs.
All side-effects (disk, network to localhost) are concentrated here
so the rest of the code remains pure and testable.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from .config import OUTPUT_DIR, VLM_MODEL
from .ocr_client import extract_text
from .schemas import DocResult, ImageResult, PipelineResult
from .unzip_and_classify import unzip_and_classify
from .vlm_client import analyze_image

console = Console()
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


def run(
    zip_path: str | Path,
    out_path: str | Path | None = None,
    verbose: bool = False,
) -> PipelineResult:
    setup_logging(verbose)
    zip_path = Path(zip_path)
    out_path = Path(out_path) if out_path else OUTPUT_DIR / "results.json"

    t_start = time.perf_counter()
    console.rule("[bold]Offline Rack Doc Analyzer")
    console.print(f"Source : {zip_path}")
    console.print(f"Model  : {VLM_MODEL}")
    console.print(f"Output : {out_path}")

    # 1. Unzip + classify
    files = unzip_and_classify(zip_path)

    images: list[ImageResult] = []
    docs: list[DocResult] = []

    # 2. Vision stage
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("VLM images", total=len(files["images"]))
        for img in files["images"]:
            progress.update(task, description=f"Analysing {Path(img).name}")
            try:
                analysis, latency = analyze_image(img)
                images.append(
                    ImageResult(
                        file=img,
                        analysis=analysis,
                        model=VLM_MODEL,
                        latency_ms=latency,
                    )
                )
            except Exception as e:
                logger.error("Image failed: %s → %s", img, e)
                images.append(ImageResult(file=img, error=str(e)))
            progress.advance(task)

        # 3. Document stage
        task2 = progress.add_task("OCR docs", total=len(files["docs"]))
        for doc in files["docs"]:
            progress.update(task2, description=f"OCR {Path(doc).name}")
            try:
                docs.append(extract_text(doc))
            except Exception as e:
                logger.error("Doc failed: %s → %s", doc, e)
                docs.append(DocResult(file=doc, status="error", error=str(e)))
            progress.advance(task2)

    elapsed = time.perf_counter() - t_start
    summary = {
        "images_total": len(images),
        "images_ok": sum(1 for i in images if i.analysis is not None),
        "images_error": sum(1 for i in images if i.error),
        "docs_total": len(docs),
        "docs_pending_ocr": sum(1 for d in docs if d.status == "pending_ocr"),
        "elapsed_sec": round(elapsed, 2),
        "vlm_model": VLM_MODEL,
    }

    result = PipelineResult(
        source_zip=str(zip_path.resolve()),
        images=images,
        docs=docs,
        summary=summary,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        result.model_dump_json(indent=2),
        encoding="utf-8",
    )

    console.rule("[bold green]Done")
    console.print(json.dumps(summary, indent=2))
    console.print(f"\nWrote → {out_path}")
    return result


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Offline rack / server-room documentation analyser"
    )
    parser.add_argument("zip", help="Path to the input zip bundle")
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output JSON path (default: output/results.json)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Debug logging",
    )
    args = parser.parse_args(argv)
    run(args.zip, args.output, args.verbose)


if __name__ == "__main__":
    main()
