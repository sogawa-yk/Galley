"""Integration tests for the Image Resize API endpoints."""

import io
import json

import pytest
from PIL import Image


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"


class TestResizeEndpoint:
    def test_resize_jpeg_with_both_dimensions(self, client, sample_jpeg):
        response = client.post(
            "/api/resize",
            data={"file": (sample_jpeg, "test.jpg"), "width": "100", "height": "50", "quality": "80"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert data["resized"]["width"] == 100
        assert data["resized"]["height"] == 50
        assert data["resized"]["quality"] == 80
        assert data["resized"]["format"] == "jpeg"
        assert "request_id" in data

    def test_resize_png_with_width_only(self, client, sample_png):
        response = client.post(
            "/api/resize",
            data={"file": (sample_png, "test.png"), "width": "150"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert data["resized"]["width"] == 150
        assert data["resized"]["format"] == "png"

    def test_resize_webp(self, client, sample_webp):
        response = client.post(
            "/api/resize",
            data={"file": (sample_webp, "test.webp"), "width": "75"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert data["resized"]["format"] == "webp"

    def test_resize_with_format_conversion(self, client, sample_jpeg):
        response = client.post(
            "/api/resize",
            data={"file": (sample_jpeg, "test.jpg"), "width": "100", "output_format": "png"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["resized"]["format"] == "png"

    def test_resize_with_height_only(self, client, sample_jpeg):
        response = client.post(
            "/api/resize",
            data={"file": (sample_jpeg, "test.jpg"), "height": "50"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert data["resized"]["height"] == 50

    def test_original_file_info_included(self, client, sample_jpeg):
        response = client.post(
            "/api/resize",
            data={"file": (sample_jpeg, "photo.jpg"), "width": "100"},
            content_type="multipart/form-data",
        )
        data = response.get_json()
        assert data["original"]["filename"] == "photo.jpg"
        assert data["original"]["size_bytes"] > 0
        assert "uploads/" in data["original"]["storage_key"]

    def test_resized_file_info_included(self, client, sample_jpeg):
        response = client.post(
            "/api/resize",
            data={"file": (sample_jpeg, "photo.jpg"), "width": "100"},
            content_type="multipart/form-data",
        )
        data = response.get_json()
        assert data["resized"]["size_bytes"] > 0
        assert "resized/" in data["resized"]["storage_key"]


class TestResizeValidation:
    def test_no_file_returns_400(self, client):
        response = client.post("/api/resize", data={"width": "100"}, content_type="multipart/form-data")
        assert response.status_code == 400
        data = response.get_json()
        assert data["code"] == "MISSING_FILE"

    def test_empty_filename_returns_400(self, client):
        response = client.post(
            "/api/resize",
            data={"file": (io.BytesIO(b""), ""), "width": "100"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400

    def test_unsupported_format_returns_400(self, client):
        buf = io.BytesIO(b"fake-bmp-data")
        response = client.post(
            "/api/resize",
            data={"file": (buf, "test.bmp"), "width": "100"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["code"] == "UNSUPPORTED_FORMAT"

    def test_missing_dimensions_returns_400(self, client, sample_jpeg):
        response = client.post(
            "/api/resize",
            data={"file": (sample_jpeg, "test.jpg")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["code"] == "MISSING_DIMENSIONS"

    def test_invalid_width_returns_400(self, client, sample_jpeg):
        response = client.post(
            "/api/resize",
            data={"file": (sample_jpeg, "test.jpg"), "width": "0"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["code"] == "INVALID_WIDTH"

    def test_width_too_large_returns_400(self, client, sample_jpeg):
        response = client.post(
            "/api/resize",
            data={"file": (sample_jpeg, "test.jpg"), "width": "5000"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["code"] == "INVALID_WIDTH"

    def test_invalid_quality_returns_400(self, client, sample_jpeg):
        response = client.post(
            "/api/resize",
            data={"file": (sample_jpeg, "test.jpg"), "width": "100", "quality": "0"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["code"] == "INVALID_QUALITY"

    def test_unsupported_output_format_returns_400(self, client, sample_jpeg):
        response = client.post(
            "/api/resize",
            data={"file": (sample_jpeg, "test.jpg"), "width": "100", "output_format": "tiff"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["code"] == "UNSUPPORTED_OUTPUT_FORMAT"

    def test_invalid_image_data_returns_400(self, client):
        buf = io.BytesIO(b"this-is-not-an-image")
        response = client.post(
            "/api/resize",
            data={"file": (buf, "test.jpg"), "width": "100"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["code"] == "PROCESSING_ERROR"

    def test_default_quality_is_85(self, client, sample_jpeg):
        response = client.post(
            "/api/resize",
            data={"file": (sample_jpeg, "test.jpg"), "width": "100"},
            content_type="multipart/form-data",
        )
        data = response.get_json()
        assert data["resized"]["quality"] == 85
