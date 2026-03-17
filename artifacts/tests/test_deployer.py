"""Tests for deployer module."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from src.deployer import save_endpoints


class TestSaveEndpoints:
    """Tests for save_endpoints function."""

    def test_saves_endpoints_correctly(self, tmp_path):
        output_path = str(tmp_path / "endpoints.json")

        result = save_endpoints(
            url="http://1.2.3.4:8080",
            project_name="test-project",
            compute_type="container_instances",
            output_path=output_path,
        )

        assert result == output_path
        with open(output_path) as f:
            data = json.load(f)

        assert data["url"] == "http://1.2.3.4:8080"
        assert data["health_url"] == "http://1.2.3.4:8080/health"
        assert data["compute_type"] == "container_instances"
        assert data["project_name"] == "test-project"

    def test_health_url_derived_from_url(self, tmp_path):
        output_path = str(tmp_path / "endpoints.json")

        save_endpoints(
            url="https://example.com",
            project_name="test",
            compute_type="oke",
            output_path=output_path,
        )

        with open(output_path) as f:
            data = json.load(f)
        assert data["health_url"] == "https://example.com/health"
