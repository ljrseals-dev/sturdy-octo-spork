"""
Unzip + classify stage.

Design note for future scientists
---------------------------------
We deliberately separate physical extraction from semantic classification.
A future version can replace the simple extension map with a lightweight
content-type model (e.g. magic-byte + small CNN) without touching the
rest of the pipeline.
"""

from __future__ import annotations

import logging
import shutil
import zipfile
from pathlib import Path

from .config import DOC_EXT, EXTRACT_DIR, IMAGE_EXT

logger = logging.getLogger(__name__)


def unzip_and_classify(
    zip_path: str | Path,
    workdir: str | Path | None = None,
) -> dict[str, list[str]]:
    """
    Unzip an archive and sort files into images/ and docs/.

    Returns
    -------
    dict with keys "images", "docs", "other" containing absolute paths.
    """
    zip_path = Path(zip_path)
    if not zip_path.is_file():
        raise FileNotFoundError(f"Zip not found: {zip_path}")

    out = Path(workdir) if workdir else EXTRACT_DIR
    img_dir = out / "images"
    doc_dir = out / "docs"
    raw_dir = out / "_raw"

    # Clean previous extraction so we never mix runs
    if out.exists():
        shutil.rmtree(out)
    img_dir.mkdir(parents=True, exist_ok=True)
    doc_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Extracting %s → %s", zip_path, raw_dir)
    with zipfile.ZipFile(zip_path) as zf:
        # Basic safety: refuse path traversal
        for info in zf.infolist():
            if Path(info.filename).is_absolute() or ".." in Path(info.filename).parts:
                raise ValueError(f"Unsafe path inside zip: {info.filename}")
        zf.extractall(raw_dir)

    result: dict[str, list[str]] = {"images": [], "docs": [], "other": []}

    for f in raw_dir.rglob("*"):
        if not f.is_file():
            continue
        ext = f.suffix.lower()
        if ext in IMAGE_EXT:
            dest = img_dir / f.name
            # Collision handling: keep both by adding a counter
            if dest.exists():
                stem, suffix = f.stem, f.suffix
                i = 1
                while dest.exists():
                    dest = img_dir / f"{stem}_{i}{suffix}"
                    i += 1
            shutil.move(str(f), str(dest))
            result["images"].append(str(dest.resolve()))
        elif ext in DOC_EXT:
            dest = doc_dir / f.name
            if dest.exists():
                stem, suffix = f.stem, f.suffix
                i = 1
                while dest.exists():
                    dest = doc_dir / f"{stem}_{i}{suffix}"
                    i += 1
            shutil.move(str(f), str(dest))
            result["docs"].append(str(dest.resolve()))
        else:
            result["other"].append(str(f.resolve()))

    logger.info(
        "Classified %d images, %d docs, %d other",
        len(result["images"]),
        len(result["docs"]),
        len(result["other"]),
    )
    return result
