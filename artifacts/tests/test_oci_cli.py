"""Tests for oci_cli module.

Note: These tests mock subprocess and HTTP calls since they require
an actual OCI environment with instance principal authentication.
"""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from src.oci_cli import (
    get_compartment_id,
    get_region,
    run_command,
)


class TestRunCommand:
    """Tests for run_command function."""

    @patch("src.oci_cli.subprocess.run")
    def test_successful_command(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"data": {"id": "ocid1.test"}}),
            stderr="",
        )
        result = run_command(["iam", "region", "list"])
        assert result["data"]["id"] == "ocid1.test"
        mock_run.assert_called_once()

    @patch("src.oci_cli.subprocess.run")
    def test_failed_command_raises(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="ServiceError: 404",
        )
        with pytest.raises(RuntimeError, match="OCI CLI failed"):
            run_command(["compute", "instance", "get", "--instance-id", "bad"])

    @patch("src.oci_cli.subprocess.run")
    def test_empty_output(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="",
        )
        result = run_command(["iam", "region", "list"])
        assert result == {}


class TestGetCompartmentId:
    """Tests for get_compartment_id function."""

    @patch("src.oci_cli.get_instance_metadata")
    def test_from_instance_metadata(self, mock_metadata):
        mock_metadata.return_value = {"compartmentId": "ocid1.compartment.test"}
        assert get_compartment_id() == "ocid1.compartment.test"

    @patch("src.oci_cli.get_instance_metadata")
    def test_from_env_var(self, mock_metadata):
        mock_metadata.side_effect = Exception("not on OCI")
        with patch.dict(os.environ, {"OCI_COMPARTMENT_ID": "ocid1.env.test"}):
            assert get_compartment_id() == "ocid1.env.test"

    @patch("src.oci_cli.get_instance_metadata")
    def test_raises_when_unresolvable(self, mock_metadata):
        mock_metadata.side_effect = Exception("not on OCI")
        with patch.dict(os.environ, {}, clear=True):
            env = os.environ.copy()
            env.pop("OCI_COMPARTMENT_ID", None)
            with patch.dict(os.environ, env, clear=True):
                with pytest.raises(RuntimeError, match="Could not resolve compartment"):
                    get_compartment_id()


class TestGetRegion:
    """Tests for get_region function."""

    @patch("src.oci_cli.get_instance_metadata")
    def test_from_instance_metadata(self, mock_metadata):
        mock_metadata.return_value = {"canonicalRegionName": "ap-tokyo-1"}
        assert get_region() == "ap-tokyo-1"

    @patch("src.oci_cli.get_instance_metadata")
    def test_from_env_var(self, mock_metadata):
        mock_metadata.side_effect = Exception("not on OCI")
        with patch.dict(os.environ, {"OCI_REGION": "us-ashburn-1"}):
            assert get_region() == "us-ashburn-1"
