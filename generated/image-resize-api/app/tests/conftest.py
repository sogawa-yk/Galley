"""Shared test fixtures for Image Resize API."""

import io

import pytest
from PIL import Image

from app import create_app


@pytest.fixture
def app():
    """Create a test Flask application."""
    app = create_app(testing=True)
    yield app


@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()


@pytest.fixture
def sample_jpeg():
    """Generate a small JPEG image for testing."""
    img = Image.new("RGB", (200, 100), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    buf.seek(0)
    return buf


@pytest.fixture
def sample_png():
    """Generate a small PNG image with alpha channel for testing."""
    img = Image.new("RGBA", (300, 200), color=(0, 255, 0, 128))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


@pytest.fixture
def sample_webp():
    """Generate a small WebP image for testing."""
    img = Image.new("RGB", (150, 150), color=(0, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=80)
    buf.seek(0)
    return buf
