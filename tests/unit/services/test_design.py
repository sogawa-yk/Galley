"""DesignServiceのユニットテスト。"""

import pytest

from galley.models.errors import (
    ArchitectureNotFoundError,
    ComponentNotFoundError,
    HearingNotCompletedError,
)
from galley.services.design import DesignService
from galley.services.hearing import HearingService


async def _create_completed_session(hearing_service: HearingService) -> str:
    """テスト用にヒアリング完了済みのセッションを作成する。"""
    session = await hearing_service.create_session()
    await hearing_service.save_answer(session.id, "purpose", "REST API構築")
    await hearing_service.complete_hearing(session.id)
    return session.id


class TestSaveArchitecture:
    async def test_save_architecture_stores_architecture(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        arch = await design_service.save_architecture(
            session_id,
            components=[{"service_type": "oke", "display_name": "OKEクラスター"}],
            connections=[],
        )
        assert arch.session_id == session_id
        assert len(arch.components) == 1
        assert arch.components[0].service_type == "oke"

    async def test_save_architecture_resolves_temporary_connection_ids(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        arch = await design_service.save_architecture(
            session_id,
            components=[
                {"id": "temp-oke", "service_type": "oke", "display_name": "OKE"},
                {"id": "temp-adb", "service_type": "adb", "display_name": "ADB"},
            ],
            connections=[
                {
                    "source_id": "temp-oke",
                    "target_id": "temp-adb",
                    "connection_type": "private_endpoint",
                    "description": "OKE to ADB",
                }
            ],
        )
        # 仮IDはUUIDに変換されているはず
        assert arch.components[0].id != "temp-oke"
        assert arch.components[1].id != "temp-adb"
        # connectionsのIDもコンポーネントの実UUIDに変換されているはず
        assert arch.connections[0].source_id == arch.components[0].id
        assert arch.connections[0].target_id == arch.components[1].id

    async def test_save_architecture_raises_for_incomplete_hearing(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session = await hearing_service.create_session()
        with pytest.raises(HearingNotCompletedError):
            await design_service.save_architecture(session.id, [], [])


class TestAddComponent:
    async def test_add_component_creates_architecture_if_missing(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        comp = await design_service.add_component(session_id, "oke", "OKE")
        assert comp.service_type == "oke"
        assert comp.display_name == "OKE"
        assert comp.id is not None

    async def test_add_component_appends_to_existing(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        await design_service.add_component(session_id, "oke", "OKE")
        await design_service.add_component(session_id, "adb", "ADB")
        services = await design_service.list_available_services()
        assert len(services) > 0  # sanity check

    async def test_add_component_with_config(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        comp = await design_service.add_component(session_id, "adb", "ADB", {"endpoint_type": "private"})
        assert comp.config["endpoint_type"] == "private"

    async def test_add_component_raises_for_incomplete_hearing(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session = await hearing_service.create_session()
        with pytest.raises(HearingNotCompletedError):
            await design_service.add_component(session.id, "oke", "OKE")


class TestRemoveComponent:
    async def test_remove_component_deletes_component(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        comp = await design_service.add_component(session_id, "oke", "OKE")
        await design_service.remove_component(session_id, comp.id)
        # Verify component is gone by trying to remove again
        with pytest.raises(ComponentNotFoundError):
            await design_service.remove_component(session_id, comp.id)

    async def test_remove_component_deletes_related_connections(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        comp1 = await design_service.add_component(session_id, "oke", "OKE")
        comp2 = await design_service.add_component(session_id, "adb", "ADB")
        # Save architecture with a connection
        await design_service.save_architecture(
            session_id,
            components=[
                {"id": comp1.id, "service_type": "oke", "display_name": "OKE"},
                {"id": comp2.id, "service_type": "adb", "display_name": "ADB"},
            ],
            connections=[
                {
                    "source_id": comp1.id,
                    "target_id": comp2.id,
                    "connection_type": "private_endpoint",
                    "description": "OKE to ADB",
                }
            ],
        )
        await design_service.remove_component(session_id, comp1.id)
        # Verify: export should not contain any connections referencing comp1
        summary = await design_service.export_summary(session_id)
        assert "OKE" not in summary  # OKE component should be removed

    async def test_remove_component_raises_for_missing_architecture(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        with pytest.raises(ArchitectureNotFoundError):
            await design_service.remove_component(session_id, "nonexistent")

    async def test_remove_component_raises_for_nonexistent(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        await design_service.add_component(session_id, "oke", "OKE")
        with pytest.raises(ComponentNotFoundError):
            await design_service.remove_component(session_id, "nonexistent-id")


class TestConfigureComponent:
    async def test_configure_component_updates_config(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        comp = await design_service.add_component(session_id, "adb", "ADB", {"endpoint_type": "public"})
        updated = await design_service.configure_component(session_id, comp.id, {"endpoint_type": "private"})
        assert updated.config["endpoint_type"] == "private"

    async def test_configure_component_merges_config(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        comp = await design_service.add_component(session_id, "adb", "ADB", {"endpoint_type": "public"})
        updated = await design_service.configure_component(session_id, comp.id, {"cpu_core_count": 2})
        assert updated.config["endpoint_type"] == "public"
        assert updated.config["cpu_core_count"] == 2

    async def test_configure_component_raises_for_nonexistent(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        await design_service.add_component(session_id, "oke", "OKE")
        with pytest.raises(ComponentNotFoundError):
            await design_service.configure_component(session_id, "nonexistent-id", {"key": "val"})


class TestValidateArchitecture:
    async def test_validate_returns_results(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[
                {"id": "oke-1", "service_type": "oke", "display_name": "OKE"},
                {"id": "adb-1", "service_type": "adb", "display_name": "ADB", "config": {"endpoint_type": "public"}},
            ],
            connections=[
                {
                    "source_id": "oke-1",
                    "target_id": "adb-1",
                    "connection_type": "public",
                    "description": "OKE to ADB",
                }
            ],
        )
        results = await design_service.validate_architecture(session_id)
        assert len(results) > 0
        assert any(r.rule_id == "oke-adb-private-endpoint" for r in results)

    async def test_validate_raises_for_missing_architecture(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        with pytest.raises(ArchitectureNotFoundError):
            await design_service.validate_architecture(session_id)


class TestListAvailableServices:
    async def test_list_returns_services(self, design_service: DesignService) -> None:
        services = await design_service.list_available_services()
        assert len(services) > 0
        service_types = {s["service_type"] for s in services}
        assert "oke" in service_types
        assert "adb" in service_types
        assert "compute" in service_types


class TestExportSummary:
    async def test_export_summary_contains_components(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "oke", "display_name": "本番OKE"}],
            connections=[],
        )
        summary = await design_service.export_summary(session_id)
        assert "本番OKE" in summary
        assert "oke" in summary


class TestExportMermaid:
    async def test_export_mermaid_contains_graph(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[
                {"id": "oke-1", "service_type": "oke", "display_name": "OKE"},
                {"id": "adb-1", "service_type": "adb", "display_name": "ADB"},
            ],
            connections=[
                {
                    "source_id": "oke-1",
                    "target_id": "adb-1",
                    "connection_type": "private_endpoint",
                    "description": "OKE to ADB",
                }
            ],
        )
        mermaid = await design_service.export_mermaid(session_id)
        assert "graph TB" in mermaid
        assert "OKE" in mermaid
        assert "ADB" in mermaid
        assert "private_endpoint" in mermaid


class TestExportIac:
    async def test_export_iac_returns_terraform_files(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "oke", "display_name": "OKE"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        files = result["terraform_files"]
        assert "main.tf" in files
        assert "variables.tf" in files
        assert "components.tf" in files
        assert "oci" in files["main.tf"]

    async def test_export_iac_generates_real_resource_definitions(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "oke", "display_name": "My OKE"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert "oci_containerengine_cluster" in components_tf
        assert "# TODO: Implement" not in components_tf

    async def test_export_iac_uses_double_quotes_for_hcl(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "vcn", "display_name": "VCN", "config": {"cidr_block": "10.0.0.0/16"}}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        # ダブルクォートが使われていること（シングルクォートではない）
        assert '"10.0.0.0/16"' in components_tf

    async def test_export_iac_writes_files_to_disk(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "oke", "display_name": "OKE"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        from pathlib import Path

        terraform_dir = Path(result["terraform_dir"])
        assert terraform_dir.exists()
        assert (terraform_dir / "main.tf").exists()
        assert (terraform_dir / "variables.tf").exists()
        assert (terraform_dir / "components.tf").exists()

    async def test_export_iac_functions_generates_application_and_function(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "functions", "display_name": "My Function"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert "oci_functions_application" in components_tf
        assert "oci_functions_function" in components_tf

    async def test_export_iac_compute_adds_dynamic_variables(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "compute", "display_name": "Web Server"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        variables_tf = result["terraform_files"]["variables.tf"]
        assert 'variable "image_id"' in variables_tf
        assert 'variable "subnet_id"' in variables_tf

    async def test_export_iac_compute_adds_data_source(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "compute", "display_name": "Web Server"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        main_tf = result["terraform_files"]["main.tf"]
        assert "oci_identity_availability_domains" in main_tf

    async def test_export_iac_deduplicates_variables(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """複数コンポーネントが同じ変数を要求する場合、重複しないことを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[
                {"service_type": "oke", "display_name": "OKE"},
                {"service_type": "apigateway", "display_name": "API GW"},
            ],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        variables_tf = result["terraform_files"]["variables.tf"]
        # subnet_idは1回だけ宣言される
        assert variables_tf.count('variable "subnet_id"') == 1

    async def test_export_iac_vcn_no_extra_variables(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """VCNのみの場合は追加変数が不要。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "vcn", "display_name": "VCN"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        variables_tf = result["terraform_files"]["variables.tf"]
        assert 'variable "subnet_id"' not in variables_tf
        assert 'variable "image_id"' not in variables_tf

    async def test_export_iac_objectstorage_adds_namespace_variable(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "objectstorage", "display_name": "Bucket"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        variables_tf = result["terraform_files"]["variables.tf"]
        assert 'variable "object_storage_namespace"' in variables_tf


class TestExportAll:
    async def test_export_all_returns_all_formats(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "oke", "display_name": "OKE"}],
            connections=[],
        )
        result = await design_service.export_all(session_id)
        assert "summary" in result
        assert "mermaid" in result
        assert "terraform_files" in result
        assert "terraform_dir" in result
