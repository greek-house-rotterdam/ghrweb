from pathlib import Path
from unittest.mock import patch

import pytest

from image_qa import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_BLOCK,
    MAX_FILE_SIZE_WARN,
    check_file_size,
    check_format,
    check_resolution,
    find_images,
)


# ---------------------------------------------------------------------------
# check_format
# ---------------------------------------------------------------------------


class TestCheckFormat:
    @pytest.mark.parametrize("ext", [".jpg", ".jpeg", ".png", ".webp"])
    def test_allowed_formats_return_none(self, ext, tmp_path):
        img = tmp_path / f"photo{ext}"
        img.touch()
        assert check_format(img) is None

    @pytest.mark.parametrize("ext", [".gif", ".bmp", ".svg", ".tiff", ".pdf"])
    def test_disallowed_formats_return_error(self, ext, tmp_path):
        img = tmp_path / f"photo{ext}"
        img.touch()
        result = check_format(img)
        assert result is not None
        assert "Unsupported format" in result

    def test_case_insensitive_via_suffix(self, tmp_path):
        """check_format uses path.suffix.lower(), so .JPG should work."""
        img = tmp_path / "photo.JPG"
        img.touch()
        # The function checks path.suffix.lower()
        assert check_format(img) is None


# ---------------------------------------------------------------------------
# check_file_size
# ---------------------------------------------------------------------------


class TestCheckFileSize:
    def test_under_limit_returns_none(self, tmp_path):
        img = tmp_path / "small.jpg"
        img.write_bytes(b"x" * 1000)  # 1 KB
        msg, blocking = check_file_size(img)
        assert msg is None
        assert blocking is False

    def test_over_warn_returns_warning(self, tmp_path):
        img = tmp_path / "medium.jpg"
        img.write_bytes(b"x" * (MAX_FILE_SIZE_WARN + 1))
        msg, blocking = check_file_size(img)
        assert msg is not None
        assert "large" in msg.lower()
        assert blocking is False

    def test_over_block_returns_blocking_error(self, tmp_path):
        img = tmp_path / "huge.jpg"
        img.write_bytes(b"x" * (MAX_FILE_SIZE_BLOCK + 1))
        msg, blocking = check_file_size(img)
        assert msg is not None
        assert "too large" in msg.lower()
        assert blocking is True

    def test_exactly_at_warn_threshold_is_ok(self, tmp_path):
        img = tmp_path / "exact.jpg"
        img.write_bytes(b"x" * MAX_FILE_SIZE_WARN)
        msg, blocking = check_file_size(img)
        assert msg is None
        assert blocking is False


# ---------------------------------------------------------------------------
# check_resolution
# ---------------------------------------------------------------------------


class TestCheckResolution:
    def _make_image(self, tmp_path, name, width, height):
        from PIL import Image

        img = Image.new("RGB", (width, height), color="red")
        path = tmp_path / name
        img.save(path)
        return path

    def test_within_bounds_returns_none(self, tmp_path):
        path = self._make_image(tmp_path, "ok.jpg", 1920, 1080)
        msg, blocking = check_resolution(path)
        assert msg is None
        assert blocking is False

    def test_too_large_returns_warning(self, tmp_path):
        path = self._make_image(tmp_path, "big.jpg", 5000, 3000)
        msg, blocking = check_resolution(path)
        assert msg is not None
        assert "too high" in msg.lower()
        assert blocking is False

    def test_too_small_returns_warning(self, tmp_path):
        path = self._make_image(tmp_path, "tiny.jpg", 100, 100)
        msg, blocking = check_resolution(path)
        assert msg is not None
        assert "too low" in msg.lower()
        assert blocking is False

    def test_exactly_at_min_is_ok(self, tmp_path):
        path = self._make_image(tmp_path, "min.jpg", 800, 600)
        msg, blocking = check_resolution(path)
        assert msg is None

    def test_exactly_at_max_is_ok(self, tmp_path):
        path = self._make_image(tmp_path, "max.jpg", 4096, 4096)
        msg, blocking = check_resolution(path)
        assert msg is None

    def test_corrupt_file_returns_blocking_error(self, tmp_path):
        path = tmp_path / "corrupt.jpg"
        path.write_bytes(b"not an image")
        msg, blocking = check_resolution(path)
        assert msg is not None
        assert blocking is True


# ---------------------------------------------------------------------------
# find_images
# ---------------------------------------------------------------------------


class TestFindImages:
    def test_filters_by_extension_when_paths_given(self):
        paths = ["photo.jpg", "doc.pdf", "icon.png", "data.csv", "pic.webp"]
        result = find_images(paths)
        names = {p.name for p in result}
        assert names == {"photo.jpg", "icon.png", "pic.webp"}

    def test_excludes_non_image_extensions(self):
        paths = ["report.pdf", "style.css", "script.js"]
        result = find_images(paths)
        assert result == []

    def test_returns_empty_when_no_paths_and_dir_missing(self, tmp_path):
        with patch("image_qa.IMAGES_DIR", tmp_path / "nonexistent"):
            result = find_images()
        assert result == []

    def test_scans_directory_when_no_paths(self, tmp_path):
        img_dir = tmp_path / "images"
        img_dir.mkdir()
        (img_dir / "a.jpg").touch()
        (img_dir / "b.png").touch()
        (img_dir / "readme.txt").touch()  # not an image

        with patch("image_qa.IMAGES_DIR", img_dir):
            result = find_images()

        names = {p.name for p in result}
        assert "a.jpg" in names
        assert "b.png" in names
        assert "readme.txt" not in names
