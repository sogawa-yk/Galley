"""ArchitectureValidatorのユニットテスト。"""

from pathlib import Path

from galley.models.architecture import Architecture, Component, Connection
from galley.validators.architecture import ArchitectureValidator


class TestArchitectureValidator:
    def _make_validator(self, config_dir: Path) -> ArchitectureValidator:
        return ArchitectureValidator(config_dir=config_dir)

    def test_validate_empty_architecture(self, config_dir: Path) -> None:
        validator = self._make_validator(config_dir)
        arch = Architecture(session_id="s1")
        results = validator.validate(arch)
        assert results == []

    def test_validate_no_violations(self, config_dir: Path) -> None:
        validator = self._make_validator(config_dir)
        oke = Component(id="oke-1", service_type="oke", display_name="OKE")
        adb = Component(
            id="adb-1",
            service_type="adb",
            display_name="ADB",
            config={"endpoint_type": "private"},
        )
        conn = Connection(
            source_id="oke-1",
            target_id="adb-1",
            connection_type="private_endpoint",
            description="OKE to ADB",
        )
        arch = Architecture(session_id="s1", components=[oke, adb], connections=[conn])
        results = validator.validate(arch)
        # endpoint_type is "private" so no violation for oke-adb-private-endpoint rule
        error_results = [r for r in results if r.severity == "error"]
        assert len(error_results) == 0

    def test_validate_detects_missing_private_endpoint(self, config_dir: Path) -> None:
        validator = self._make_validator(config_dir)
        oke = Component(id="oke-1", service_type="oke", display_name="OKE")
        adb = Component(
            id="adb-1",
            service_type="adb",
            display_name="ADB",
            config={"endpoint_type": "public"},
        )
        conn = Connection(
            source_id="oke-1",
            target_id="adb-1",
            connection_type="public",
            description="OKE to ADB",
        )
        arch = Architecture(session_id="s1", components=[oke, adb], connections=[conn])
        results = validator.validate(arch)
        error_results = [r for r in results if r.severity == "error"]
        assert len(error_results) == 1
        assert error_results[0].rule_id == "oke-adb-private-endpoint"
        assert "oke-1" in error_results[0].affected_components
        assert "adb-1" in error_results[0].affected_components

    def test_validate_no_rules_directory(self, tmp_path: Path) -> None:
        # config_dirにvalidation-rulesが無い場合はエラーなし
        validator = self._make_validator(tmp_path)
        arch = Architecture(session_id="s1")
        results = validator.validate(arch)
        assert results == []

    def test_validate_unrelated_connection(self, config_dir: Path) -> None:
        validator = self._make_validator(config_dir)
        apigw = Component(id="apigw-1", service_type="apigateway", display_name="API GW")
        fn = Component(id="fn-1", service_type="functions", display_name="Functions")
        conn = Connection(
            source_id="apigw-1",
            target_id="fn-1",
            connection_type="public",
            description="API GW to Functions",
        )
        arch = Architecture(session_id="s1", components=[apigw, fn], connections=[conn])
        results = validator.validate(arch)
        # apigateway -> functions connection: info level only, no errors
        error_results = [r for r in results if r.severity == "error"]
        assert len(error_results) == 0
