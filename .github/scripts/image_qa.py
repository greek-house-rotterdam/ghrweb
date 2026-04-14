#!/usr/bin/env python3
"""
Image technical QA — validates and optimizes images in public/images/.

Checks:
  - Format: JPEG, PNG, or WebP only
  - File size: warn >2 MB, hard block >5 MB
  - Resolution: min 800x600, max 4096x4096

Auto-optimization (when Pillow is available):
  - Resize images exceeding max resolution
  - Compress to WebP if >2 MB
  - Skip if already within limits

Exit code 1 if any image fails hard limits.
"""

import sys
from pathlib import Path

try:
    from PIL import Image

    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

IMAGES_DIR = Path("public/images")

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE_WARN = 2 * 1024 * 1024  # 2 MB
MAX_FILE_SIZE_BLOCK = 5 * 1024 * 1024  # 5 MB
MIN_WIDTH, MIN_HEIGHT = 800, 600
MAX_WIDTH, MAX_HEIGHT = 4096, 4096


def find_images(paths: list[str] | None = None) -> list[Path]:
    """Find images to check. If paths given, use those. Otherwise scan IMAGES_DIR."""
    if paths:
        return [Path(p) for p in paths if Path(p).suffix.lower() in ALLOWED_EXTENSIONS]

    if not IMAGES_DIR.exists():
        return []
    return [
        f
        for f in IMAGES_DIR.rglob("*")
        if f.is_file() and f.suffix.lower() in ALLOWED_EXTENSIONS
    ]


def check_format(path: Path) -> str | None:
    ext = path.suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return f"Unsupported format: {ext} (allowed: {', '.join(ALLOWED_EXTENSIONS)})"
    return None


def check_file_size(path: Path) -> tuple[str | None, bool]:
    """Returns (message, is_blocking)."""
    size = path.stat().st_size
    if size > MAX_FILE_SIZE_BLOCK:
        return f"File too large: {size / 1024 / 1024:.1f} MB (max {MAX_FILE_SIZE_BLOCK / 1024 / 1024:.0f} MB)", True
    if size > MAX_FILE_SIZE_WARN:
        return f"File large: {size / 1024 / 1024:.1f} MB (recommended max {MAX_FILE_SIZE_WARN / 1024 / 1024:.0f} MB)", False
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


def optimize_image(path: Path) -> bool:
    """Try to auto-optimize an image. Returns True if modified."""
    if not HAS_PILLOW:
        return False

    modified = False
    try:
        with Image.open(path) as img:
            w, h = img.size

            # Resize if exceeds max
            if w > MAX_WIDTH or h > MAX_HEIGHT:
                ratio = min(MAX_WIDTH / w, MAX_HEIGHT / h)
                new_size = (int(w * ratio), int(h * ratio))
                img = img.resize(new_size, Image.LANCZOS)
                print(f"  Resized: {w}x{h} → {new_size[0]}x{new_size[1]}")
                modified = True

            # Convert to WebP if file is too large
            size = path.stat().st_size
            if size > MAX_FILE_SIZE_WARN:
                webp_path = path.with_suffix(".webp")
                img.save(webp_path, "WEBP", quality=85)
                if webp_path != path:
                    path.unlink()
                    print(f"  Converted to WebP: {webp_path.name} ({webp_path.stat().st_size / 1024:.0f} KB)")
                modified = True
            elif modified:
                img.save(path, quality=90)
    except Exception as e:
        print(f"  Optimization failed: {e}")
        return False

    return modified


def main():
    # Accept file paths as arguments (from git diff), or scan directory
    paths = sys.argv[1:] if len(sys.argv) > 1 else None
    images = find_images(paths)

    if not images:
        print("No images to check.")
        return

    if not HAS_PILLOW:
        print("Warning: Pillow not installed — skipping resolution checks and auto-optimization.")
        print("Install with: pip install Pillow")

    errors = 0
    warnings = 0

    for img_path in images:
        if not img_path.exists():
            continue

        issues: list[str] = []
        blocking = False

        # Format check
        fmt_err = check_format(img_path)
        if fmt_err:
            issues.append(f"BLOCK: {fmt_err}")
            blocking = True

        # File size check
        size_msg, size_block = check_file_size(img_path)
        if size_msg:
            if size_block:
                issues.append(f"BLOCK: {size_msg}")
                blocking = True
            else:
                issues.append(f"WARN: {size_msg}")

        # Resolution check
        res_msg, res_block = check_resolution(img_path)
        if res_msg:
            if res_block:
                issues.append(f"BLOCK: {res_msg}")
                blocking = True
            else:
                issues.append(f"WARN: {res_msg}")

        if issues:
            print(f"\n{img_path}:")
            for issue in issues:
                print(f"  {issue}")
                if issue.startswith("BLOCK"):
                    errors += 1
                else:
                    warnings += 1

            # Try auto-optimization for warnings (not blocking errors)
            if not blocking and HAS_PILLOW:
                optimized = optimize_image(img_path)
                if optimized:
                    print("  → Auto-optimized")

    print(f"\nSummary: {len(images)} images checked, {errors} errors, {warnings} warnings")

    if errors > 0:
        print("FAILED: Fix blocking errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
