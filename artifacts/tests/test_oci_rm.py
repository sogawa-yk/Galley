"""Tests for oci_rm module."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.oci_rm import (
    save_stack_outputs,
    zip_terraform_dir,
)


class TestZipTerraformDir:
    """Tests for zip_terraform_dir function."""

    def test_creates_zip_from_tf_files(self, tmp_path):
        tf_dir = tmp_path / "terraform"
        tf_dir.mkdir()
        (tf_dir / "main.tf").write_text('resource "null" "test" {}')
        (tf_dir / "variables.tf").write_text('variable "x" {}')
        (tf_dir / "terraform.tfvars").write_text('x = "hello"')

        zip_path = zip_terraform_dir(str(tf_dir))

        assert os.path.exists(zip_path)
        assert zip_path.endswith("terraform.zip")

        import zipfile
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            assert "main.tf" in names
            assert "variables.tf" in names
            assert "terraform.tfvars" in names

    def test_raises_on_missing_dir(self):
        with pytest.raises(FileNotFoundError):
            zip_terraform_dir("/nonexistent/path")

    def test_raises_on_no_tf_files(self, tmp_path):
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        (empty_dir / "readme.md").write_text("not a tf file")

        with pytest.raises(ValueError, match="No .tf files"):
            zip_terraform_dir(str(empty_dir))

    def test_includes_sh_files(self, tmp_path):
        tf_dir = tmp_path / "terraform"
        tf_dir.mkdir()
        (tf_dir / "main.tf").write_text('resource "null" "test" {}')
        (tf_dir / "cloud-init.sh").write_text("#!/bin/bash")

        zip_path = zip_terraform_dir(str(tf_dir))

        import zipfile
        with zipfile.ZipFile(zip_path) as zf:
            assert "cloud-init.sh" in zf.namelist()

    def test_flat_structure(self, tmp_path):
        tf_dir = tmp_path / "terraform"
        tf_dir.mkdir()
        (tf_dir / "main.tf").write_text('resource "null" "test" {}')

        zip_path = zip_terraform_dir(str(tf_dir))

        import zipfile
        with zipfile.ZipFile(zip_path) as zf:
            for name in zf.namelist():
                assert "/" not in name  # No subdirectory nesting


class TestSaveStackOutputs:
    """Tests for save_stack_outputs function."""

    def test_saves_outputs_with_metadata(self, tmp_path):
        output_path = str(tmp_path / "stack_outputs.json")
        outputs = {"vcn_id": "ocid1.vcn.test", "public_ip": "1.2.3.4"}

        result = save_stack_outputs(
            outputs=outputs,
            stack_id="ocid1.stack.test",
            job_id="ocid1.job.test",
            project_name="test-project",
            output_path=output_path,
        )

        assert result == output_path
        with open(output_path) as f:
            data = json.load(f)

        assert data["vcn_id"] == "ocid1.vcn.test"
        assert data["public_ip"] == "1.2.3.4"
        assert data["_stack_id"] == "ocid1.stack.test"
        assert data["_apply_job_id"] == "ocid1.job.test"
        assert data["_project_name"] == "test-project"
