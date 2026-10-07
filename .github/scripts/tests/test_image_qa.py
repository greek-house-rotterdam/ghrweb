import random
from unittest.mock import patch

import pytest
from PIL import Image, ImageCms

import image_qa
from image_qa import (
    ALLOWED_EXTENSIONS,
    MAX_FILE_SIZE_BLOCK,
    MAX_FILE_SIZE_WARN,
    MAX_HEIGHT,
    MAX_WIDTH,
    check_file_size,
    check_format,
    check_resolution,
    find_images,
    main,
    optimize_image,
)


def noise_image(width, height):
    """Random pixels: compresses badly, so small dimensions still give a big file."""
    return Image.frombytes("RGB", (width, height), random.Random(0).randbytes(width * height * 3))


# ---------------------------------------------------------------------------
# check_format
# ---------------------------------------------------------------------------


class TestCheckFormat:
    @pytest.mark.parametrize("ext", [".jpg", ".jpeg", ".png", ".webp"])
    def test_allowed_formats_return_none(self, ext, tmp_path):
        img = tmp_path / f"photo{ext}"
        img.touch()
        assert check_format(img) is None

    @pytest.mark.parametrize("ext", [".gif", ".bmp", ".svg", ".tiff", ".pdf", ".heic"])
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
        path = self._make_image(tmp_path, "big.jpg", MAX_WIDTH + 1, 1500)
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
        path = self._make_image(tmp_path, "max.jpg", MAX_WIDTH, MAX_HEIGHT)
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
    def test_keeps_every_given_path(self):
        # An unsupported file must reach check_format, not be skipped.
        paths = ["photo.jpg", "doc.pdf", "icon.png", "photo.heic"]
        assert [p.name for p in find_images(paths)] == paths

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


# ---------------------------------------------------------------------------
# optimize_image
# ---------------------------------------------------------------------------


class TestOptimizeImage:
    """Thresholds are lowered so the test images stay small and fast."""

    @pytest.fixture(autouse=True)
    def _small_limits(self, monkeypatch):
        monkeypatch.setattr(image_qa, "MAX_WIDTH", 400)
        monkeypatch.setattr(image_qa, "MAX_HEIGHT", 400)
        monkeypatch.setattr(image_qa, "MAX_FILE_SIZE_WARN", 20_000)

    def test_leaves_small_image_untouched(self, tmp_path):
        path = tmp_path / "small.jpg"
        Image.new("RGB", (300, 200), "red").save(path)
        before = path.read_bytes()
        assert optimize_image(path) is None
        assert path.read_bytes() == before

    def test_resizes_in_place_and_keeps_name_and_format(self, tmp_path):
        # Renaming the file (the old .webp conversion) broke every reference to it.
        path = tmp_path / "wide.jpg"
        Image.new("RGB", (1000, 500), "red").save(path)
        assert optimize_image(path) is not None
        assert list(tmp_path.iterdir()) == [path]
        with Image.open(path) as img:
            assert img.format == "JPEG"
            assert img.size == (400, 200)

    def test_compresses_large_file_in_place(self, tmp_path):
        path = tmp_path / "noisy.jpg"
        noise_image(300, 300).save(path, quality=100)
        before = path.stat().st_size
        assert before > image_qa.MAX_FILE_SIZE_WARN

        assert optimize_image(path) is not None
        assert path.stat().st_size < before
        with Image.open(path) as img:
            assert img.format == "JPEG"
            assert img.size == (300, 300)

    def test_png_stays_png(self, tmp_path):
        path = tmp_path / "graphic.png"
        Image.new("RGBA", (800, 400), (0, 0, 255, 128)).save(path)
        assert optimize_image(path) is not None
        with Image.open(path) as img:
            assert img.format == "PNG"
            assert img.size == (400, 200)

    def test_applies_exif_orientation_and_drops_gps(self, tmp_path):
        # Phones save portrait photos as landscape pixels plus an orientation
        # tag. Re-encoding drops EXIF, so without applying the tag first the
        # photo would turn sideways.
        path = tmp_path / "portrait.jpg"
        exif = Image.Exif()
        exif[0x0112] = 6  # rotate 90° clockwise
        exif[0x8825] = {2: (52.0, 0.0, 0.0)}  # GPS latitude
        Image.new("RGB", (800, 400), "red").save(path, exif=exif)

        optimize_image(path)
        with Image.open(path) as img:
            assert img.size == (200, 400)
            assert 0x0112 not in img.getexif()
            assert 0x8825 not in img.getexif()

    def test_keeps_colour_profile(self, tmp_path):
        # iPhone photos are Display P3; losing the profile washes out colours.
        icc = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
        path = tmp_path / "p3.jpg"
        Image.new("RGB", (800, 400), "red").save(path, icc_profile=icc)
        optimize_image(path)
        with Image.open(path) as img:
            assert img.info.get("icc_profile") == icc

    def test_does_not_recompress_an_already_optimized_file(self, tmp_path):
        # Every save of the post re-runs --fix. Re-encoding the same photo
        # each time would lose quality for almost no saving.
        path = tmp_path / "noisy.jpg"
        noise_image(300, 300).save(path, quality=100)
        assert optimize_image(path) is not None
        once = path.read_bytes()
        assert len(once) > image_qa.MAX_FILE_SIZE_WARN  # still over the limit

        assert optimize_image(path) is None
        assert path.read_bytes() == once

    def test_skips_animated_images(self, tmp_path):
        path = tmp_path / "anim.png"
        frames = [Image.new("RGB", (800, 400), c) for c in ("red", "blue")]
        frames[0].save(path, save_all=True, append_images=frames[1:])
        before = path.read_bytes()
        assert optimize_image(path) is None
        assert path.read_bytes() == before

    def test_unreadable_file_is_left_for_the_check(self, tmp_path):
        path = tmp_path / "corrupt.jpg"
        path.write_bytes(b"x" * 30_000)
        assert optimize_image(path) is None
        assert path.read_bytes() == b"x" * 30_000

    def test_ignores_unsupported_formats(self, tmp_path):
        path = tmp_path / "photo.heic"
        path.write_bytes(b"x" * 30_000)
        assert optimize_image(path) is None


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


class TestMain:
    def _jpeg(self, tmp_path, name="ok.jpg"):
        path = tmp_path / name
        Image.new("RGB", (1200, 800), "red").save(path)
        return path

    def test_check_passes_for_a_good_image(self, tmp_path):
        report = tmp_path / "report.md"
        assert main(["--report", str(report), str(self._jpeg(tmp_path))]) == 0
        assert not report.exists()

    def test_check_blocks_unsupported_format_and_reports_it(self, tmp_path):
        bad = tmp_path / "photo.heic"
        bad.write_bytes(b"heic")
        report = tmp_path / "report.md"
        assert main(["--report", str(report), str(self._jpeg(tmp_path)), str(bad)]) == 1
        text = report.read_text(encoding="utf-8")
        assert f"`{bad}`" in text
        assert "Unsupported format: .heic" in text
        assert "ok.jpg" not in text

    def test_check_blocks_unreadable_image(self, tmp_path):
        bad = tmp_path / "corrupt.png"
        bad.write_bytes(b"not an image")
        assert main([str(bad)]) == 1

    def test_report_appends_across_runs(self, tmp_path):
        # xargs may split a long file list into several invocations.
        report = tmp_path / "report.md"
        for name in ("a.gif", "b.svg"):
            bad = tmp_path / name
            bad.write_bytes(b"x")
            main(["--report", str(report), str(bad)])
        text = report.read_text(encoding="utf-8")
        assert "a.gif" in text and "b.svg" in text

    def test_fix_never_fails_on_problems_it_cannot_fix(self, tmp_path):
        # Blocking problems are the check's job (verify); --fix runs in the
        # translate job, which must still commit the translations.
        bad = tmp_path / "corrupt.jpg"
        bad.write_bytes(b"not an image")
        assert main(["--fix", str(bad), str(tmp_path / "missing.jpg")]) == 0

    def test_no_files_is_not_an_error(self, tmp_path):
        with patch("image_qa.IMAGES_DIR", tmp_path / "nonexistent"):
            assert main([]) == 0


def test_max_resolution_is_2560():
    # Documented for editors in the Decap image hint and docs/known-limitations.md.
    assert (MAX_WIDTH, MAX_HEIGHT) == (2560, 2560)


def test_save_options_cover_every_allowed_extension():
    assert set(image_qa.SAVE_AS) == ALLOWED_EXTENSIONS
