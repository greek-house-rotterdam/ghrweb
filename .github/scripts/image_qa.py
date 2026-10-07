#!/usr/bin/env python3
"""
Image technical QA for public/images/.

The Content Pipeline workflow (translate.yml) runs this in two places:

  image_qa.py --fix FILE...
      Translate job. Shrinks oversized images in place and keeps the filename
      and format, so the post's references to them keep working. The result
      goes into the same bot commit as the translations. Exits 0 unless it
      crashes; problems it can't fix are left for the check.

  image_qa.py [--report PATH] FILE...
      Verify job (a required check). Reports problems and exits 1 on a
      blocking one, which blocks publishing. --report appends the blocking
      problems as a markdown list, for the PR notice.

Blocking: a format other than JPEG, PNG or WebP; a file that can't be read
as an image; a file over 5 MB.
Warnings: over 2 MB; under 800x600; over 2560 px on either side (--fix
resizes these).
"""

import argparse
import io
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps

    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

IMAGES_DIR = Path("public/images")

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE_WARN = 2 * 1024 * 1024  # 2 MB
MAX_FILE_SIZE_BLOCK = 5 * 1024 * 1024  # 5 MB
MIN_WIDTH, MIN_HEIGHT = 800, 600
# Sharp for full-width images on high-density screens. A 24 MP phone photo
# shrinks to about 1 MB; at 4096 px it stayed over 2 MB.
MAX_WIDTH, MAX_HEIGHT = 2560, 2560

# Pillow format name and save options per extension. The format never
# changes, so the file can be overwritten under the same name.
SAVE_AS = {
    ".jpg": ("JPEG", {"quality": 85, "optimize": True, "progressive": True}),
    ".jpeg": ("JPEG", {"quality": 85, "optimize": True, "progressive": True}),
    ".png": ("PNG", {"optimize": True}),
    ".webp": ("WEBP", {"quality": 85, "method": 6}),
}

# A re-encode that saves less than this is discarded. Without it, every save
# of the post would re-compress the same photo and lose a little quality.
MIN_SAVING = 0.10


def find_images(paths: list[str] | None = None) -> list[Path]:
    """Files to check. If paths are given, use all of them, so a file in an
    unsupported format gets reported instead of skipped. Otherwise scan
    IMAGES_DIR for supported images."""
    if paths:
        return [Path(p) for p in paths]

    if not IMAGES_DIR.exists():
        return []
    return [
        f
        for f in IMAGES_DIR.rglob("*")
        if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS
    ]


def mb(size: int) -> str:
    return f"{size / 1024 / 1024:.1f} MB"


def check_format(path: Path) -> str | None:
    ext = path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        return f"Unsupported format: {ext or '(none)'} (allowed: {allowed})"
    return None


def check_file_size(path: Path) -> tuple[str | None, bool]:
    """Returns (message, is_blocking)."""
    size = path.stat().st_size
    if size > MAX_FILE_SIZE_BLOCK:
        return f"File too large: {mb(size)} (max {MAX_FILE_SIZE_BLOCK // 1024 // 1024} MB)", True
    if size > MAX_FILE_SIZE_WARN:
        return f"File large: {mb(size)} (recommended max {MAX_FILE_SIZE_WARN // 1024 // 1024} MB)", False
    return None, False


def check_resolution(path: Path) -> tuple[str | None, bool]:
    """Returns (message, is_blocking). Requires Pillow."""
    if not HAS_PILLOW:
        return None, False
    try:
        with Image.open(path) as img:
            w, h = img.size
    except Exception as e:
        return f"Cannot read image: {e}", True

    if w > MAX_WIDTH or h > MAX_HEIGHT:
        return f"Resolution too high: {w}x{h} (max {MAX_WIDTH}x{MAX_HEIGHT})", False
    if w < MIN_WIDTH or h < MIN_HEIGHT:
        return f"Resolution too low: {w}x{h} (min {MIN_WIDTH}x{MIN_HEIGHT})", False
    return None, False


def optimize_image(path: Path) -> str | None:
    """Shrink an oversized image in place. Returns what changed, or None.

    Only touches images over 2560 px on either side or over 2 MB, and
    resizes to fit 2560x2560 (aspect ratio kept). Keeps the filename,
    format and colour profile. Phones store portrait photos as landscape
    pixels plus an EXIF orientation tag, and re-encoding drops EXIF, so the
    orientation is applied to the pixels first. Dropping EXIF also removes
    the GPS location.
    """
    if not HAS_PILLOW or path.suffix.lower() not in SAVE_AS:
        return None
    fmt, options = SAVE_AS[path.suffix.lower()]
    size = path.stat().st_size

    try:
        with Image.open(path) as img:
            w, h = img.size
            too_big = w > MAX_WIDTH or h > MAX_HEIGHT
            if not too_big and size <= MAX_FILE_SIZE_WARN:
                return None
            if getattr(img, "is_animated", False):
                return None  # saving would keep only the first frame

            out = ImageOps.exif_transpose(img)
            if too_big:
                out.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.LANCZOS)

            buf = io.BytesIO()
            out.save(buf, fmt, icc_profile=img.info.get("icc_profile"), **options)
    except Exception as e:
        # An unreadable file is a blocking problem; the check reports it.
        print(f"{path}: could not optimize: {e}")
        return None

    data = buf.getvalue()
    if not too_big and len(data) > size * (1 - MIN_SAVING):
        return None

    path.write_bytes(data)
    return f"{w}x{h}, {mb(size)} → {out.width}x{out.height}, {mb(len(data))}"


def check_image(path: Path) -> tuple[list[str], list[str]]:
    """Returns (blocking problems, warnings)."""
    fmt_err = check_format(path)
    if fmt_err:
        return [fmt_err], []

    blocking: list[str] = []
    warnings: list[str] = []
    for message, is_blocking in (check_file_size(path), check_resolution(path)):
        if message:
            (blocking if is_blocking else warnings).append(message)
    return blocking, warnings


def fix(images: list[Path]) -> int:
    for img_path in images:
        if not img_path.exists():
            continue
        change = optimize_image(img_path)
        if change:
            print(f"{img_path}: optimized ({change})")
    return 0


def check(images: list[Path], report: Path | None) -> int:
    errors = 0
    warnings = 0
    problems: list[str] = []

    for img_path in images:
        if not img_path.exists():
            continue
        blocking, warns = check_image(img_path)
        if not blocking and not warns:
            continue

        print(f"\n{img_path}:")
        for message in blocking:
            print(f"  BLOCK: {message}")
            problems.append(f"- `{img_path}`: {message}")
        for message in warns:
            print(f"  WARN: {message}")
        errors += len(blocking)
        warnings += len(warns)

    print(f"\nSummary: {len(images)} images checked, {errors} errors, {warnings} warnings")

    if errors > 0:
        if report:
            # Append: xargs may split a long file list over several runs.
            with report.open("a", encoding="utf-8") as f:
                f.write("\n".join(problems) + "\n")
        print("FAILED: Fix blocking errors above.")
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check or optimize images.")
    parser.add_argument("--fix", action="store_true", help="shrink oversized images in place")
    parser.add_argument("--report", type=Path, help="append blocking problems here (markdown)")
    parser.add_argument("files", nargs="*", help="files to process (default: scan public/images)")
    args = parser.parse_args(argv)

    images = find_images(args.files or None)
    if not images:
        print("No images to check.")
        return 0

    if not HAS_PILLOW:
        print("Warning: Pillow not installed — skipping resolution checks and auto-optimization.")
        print("Install with: pip install Pillow")

    return fix(images) if args.fix else check(images, args.report)


if __name__ == "__main__":
    sys.exit(main())
