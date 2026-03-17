"""Unit tests for the ImageProcessor service."""

import io

import pytest
from PIL import Image

from services.image_processor import ImageProcessor


@pytest.fixture
def processor():
    return ImageProcessor()


@pytest.fixture
def jpeg_bytes():
    img = Image.new("RGB", (400, 300), color=(255, 128, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.getvalue()


@pytest.fixture
def png_rgba_bytes():
    img = Image.new("RGBA", (400, 300), color=(0, 128, 255, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


class TestResizeWithBothDimensions:
    def test_resize_to_exact_dimensions(self, processor, jpeg_bytes):
        result, fmt = processor.resize(jpeg_bytes, width=100, height=80)
        img = Image.open(io.BytesIO(result))
        assert img.size == (100, 80)
        assert fmt == "jpeg"

    def test_resize_preserves_format(self, processor, jpeg_bytes):
        _, fmt = processor.resize(jpeg_bytes, width=50, height=50)
        assert fmt == "jpeg"


class TestResizeWithWidthOnly:
    def test_auto_calculates_height(self, processor, jpeg_bytes):
        # Original is 400x300, width=200 => height should be 150
        result, _ = processor.resize(jpeg_bytes, width=200)
        img = Image.open(io.BytesIO(result))
        assert img.size == (200, 150)

    def test_maintains_aspect_ratio(self, processor, jpeg_bytes):
        result, _ = processor.resize(jpeg_bytes, width=100)
        img = Image.open(io.BytesIO(result))
        # 400:300 = 4:3, so 100:75
        assert img.size == (100, 75)


class TestResizeWithHeightOnly:
    def test_auto_calculates_width(self, processor, jpeg_bytes):
        # Original is 400x300, height=150 => width should be 200
        result, _ = processor.resize(jpeg_bytes, height=150)
        img = Image.open(io.BytesIO(result))
        assert img.size == (200, 150)


class TestOutputFormatConversion:
    def test_jpeg_to_png(self, processor, jpeg_bytes):
        result, fmt = processor.resize(jpeg_bytes, width=100, output_format="png")
        assert fmt == "png"
        img = Image.open(io.BytesIO(result))
        assert img.format == "PNG"

    def test_jpeg_to_webp(self, processor, jpeg_bytes):
        result, fmt = processor.resize(jpeg_bytes, width=100, output_format="webp")
        assert fmt == "webp"

    def test_png_rgba_to_jpeg_converts_to_rgb(self, processor, png_rgba_bytes):
        result, fmt = processor.resize(png_rgba_bytes, width=100, output_format="jpeg")
        assert fmt == "jpeg"
        img = Image.open(io.BytesIO(result))
        assert img.mode == "RGB"  # Alpha removed


class TestQuality:
    def test_lower_quality_produces_smaller_file(self, processor, jpeg_bytes):
        high_q, _ = processor.resize(jpeg_bytes, width=200, quality=95)
        low_q, _ = processor.resize(jpeg_bytes, width=200, quality=10)
        assert len(low_q) < len(high_q)


class TestErrorHandling:
    def test_invalid_image_data_raises(self, processor):
        with pytest.raises(ValueError, match="Invalid image data"):
            processor.resize(b"not-an-image", width=100)

    def test_unsupported_output_format_raises(self, processor, jpeg_bytes):
        with pytest.raises(ValueError, match="Unsupported output format"):
            processor.resize(jpeg_bytes, width=100, output_format="bmp")

    def test_no_dimensions_raises(self, processor, jpeg_bytes):
        with pytest.raises(ValueError, match="At least one of width or height"):
            processor.resize(jpeg_bytes)
