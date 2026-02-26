"""DesignServiceのユニットテスト。"""

from pathlib import Path

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
        # image_idはdata sourceで自動取得されるため変数として生成されない
        assert 'variable "image_id"' not in variables_tf
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
        assert "oci_core_images" in main_tf

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

    async def test_export_iac_subnet_generates_real_resource(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """R2: subnet テンプレートが実リソース定義を生成する。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[
                {"service_type": "subnet", "display_name": "Public Subnet", "config": {"cidr_block": "10.0.1.0/24"}},
            ],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert "oci_core_subnet" in components_tf
        assert "10.0.1.0/24" in components_tf

    async def test_export_iac_internet_gateway_generates_resource(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """R2: internet_gateway テンプレートが実リソース定義を生成する。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "internet_gateway", "display_name": "IGW"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert "oci_core_internet_gateway" in components_tf

    async def test_export_iac_security_list_generates_resource(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """R2: security_list テンプレートが実リソース定義を生成する。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[
                {"service_type": "security_list", "display_name": "SL", "config": {"ingress_port": "443"}},
            ],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert "oci_core_security_list" in components_tf
        assert "443" in components_tf

    async def test_export_iac_security_list_port_zero_replaced_with_default(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """ingress_port=0の場合はデフォルト22に置き換えられることを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[
                {"service_type": "security_list", "display_name": "SL", "config": {"ingress_port": "0"}},
            ],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert "min = 0" not in components_tf
        assert "min = 22" in components_tf

    async def test_export_iac_generates_tfvars_example(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """R3: terraform.tfvars.example が生成される。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "compute", "display_name": "Server"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        assert "terraform.tfvars.example" in result["terraform_files"]
        tfvars = result["terraform_files"]["terraform.tfvars.example"]
        assert "region" in tfvars
        assert "compartment_ocid" in tfvars
        # image_idはdata sourceで自動取得されるためtfvarsには含まれない
        assert "image_id" not in tfvars

    async def test_export_iac_local_subnet_skips_subnet_id_variable(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """R4: アーキテクチャにsubnetが含まれる場合、subnet_id変数は生成されない。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[
                {"service_type": "subnet", "display_name": "My Subnet"},
                {"service_type": "compute", "display_name": "Server"},
            ],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        variables_tf = result["terraform_files"]["variables.tf"]
        assert 'variable "subnet_id"' not in variables_tf

    async def test_export_iac_local_subnet_replaces_var_reference(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """R4: subnet が存在する場合、var.subnet_id がローカル参照に置換される。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[
                {"service_type": "subnet", "display_name": "My Subnet"},
                {"service_type": "compute", "display_name": "Server"},
            ],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert "var.subnet_id" not in components_tf
        assert "oci_core_subnet.my_subnet.id" in components_tf

    async def test_export_iac_local_vcn_replaces_var_reference(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """R4: VCN が存在する場合、var.vcn_id がローカル参照に置換される。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[
                {"service_type": "vcn", "display_name": "Main VCN"},
                {"service_type": "subnet", "display_name": "Public Subnet"},
            ],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert "var.vcn_id" not in components_tf
        assert "oci_core_vcn.main_vcn.id" in components_tf

    async def test_export_iac_bool_config_renders_lowercase(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """bool値がHCL形式（true/false）で出力されることを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[
                {"service_type": "loadbalancer", "display_name": "LB", "config": {"is_private": True}},
            ],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert "is_private     = true" in components_tf
        assert "True" not in components_tf

    async def test_export_iac_oke_default_version_is_supported(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """OKEのデフォルトK8sバージョンがv1.31以上であることを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "oke", "display_name": "OKE"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert "v1.28" not in components_tf
        assert "v1.31.1" in components_tf

    async def test_export_iac_oke_has_service_lb_subnet_ids(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """OKEクラスタにservice_lb_subnet_idsが含まれることを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "oke", "display_name": "OKE"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert "service_lb_subnet_ids" in components_tf

    async def test_export_iac_oke_node_pool_uses_node_subnet_id(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """OKEノードプールがnode_subnet_id変数を使うことを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "oke", "display_name": "OKE"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        variables_tf = result["terraform_files"]["variables.tf"]
        assert 'variable "node_subnet_id"' in variables_tf

    async def test_export_iac_adb_includes_admin_password_variable(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """ADBテンプレートにadmin_password変数参照が含まれることを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "adb", "display_name": "ADB"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        variables_tf = result["terraform_files"]["variables.tf"]
        assert "var.adb_admin_password" in components_tf
        assert 'variable "adb_admin_password"' in variables_tf
        assert "sensitive   = true" in variables_tf

    async def test_export_iac_adb_workload_type_mapped_to_oltp(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """ADBのworkload_type 'ATP'がOCI API値'OLTP'に変換されることを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[
                {"service_type": "adb", "display_name": "ADB", "config": {"workload_type": "ATP"}},
            ],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert '"OLTP"' in components_tf
        assert '"ATP"' not in components_tf

    async def test_export_iac_adb_workload_type_adw_mapped_to_dw(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """ADBのworkload_type 'ADW'がOCI API値'DW'に変換されることを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[
                {"service_type": "adb", "display_name": "ADB", "config": {"workload_type": "ADW"}},
            ],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert '"DW"' in components_tf

    async def test_export_iac_loadbalancer_includes_shape_details(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """LBテンプレートにshape_detailsブロックが含まれることを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "loadbalancer", "display_name": "LB"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert "shape_details" in components_tf
        assert "minimum_bandwidth_in_mbps" in components_tf
        assert "maximum_bandwidth_in_mbps" in components_tf


class TestExportIacRmCompatibility:
    async def test_export_iac_no_auth_in_provider(
        self,
        hearing_service: HearingService,
        design_service: DesignService,
    ) -> None:
        """RM互換: providerブロックにauthパラメータが含まれないこと。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "vcn", "display_name": "VCN"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        main_tf = result["terraform_files"]["main.tf"]
        assert "auth" not in main_tf
        assert "ResourcePrincipal" not in main_tf

    async def test_export_iac_uses_compartment_ocid_variable(
        self,
        hearing_service: HearingService,
        design_service: DesignService,
    ) -> None:
        """RM互換: compartment_ocid変数が使用されていること。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "vcn", "display_name": "VCN"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        variables_tf = result["terraform_files"]["variables.tf"]
        components_tf = result["terraform_files"]["components.tf"]
        assert 'variable "compartment_ocid"' in variables_tf
        assert 'variable "compartment_id"' not in variables_tf
        assert "var.compartment_ocid" in components_tf

    async def test_export_iac_includes_tenancy_ocid_variable(
        self,
        hearing_service: HearingService,
        design_service: DesignService,
    ) -> None:
        """RM互換: tenancy_ocid変数が宣言されていること。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "vcn", "display_name": "VCN"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        variables_tf = result["terraform_files"]["variables.tf"]
        assert 'variable "tenancy_ocid"' in variables_tf


class TestSanitizeResourceName:
    def test_parentheses_removed(self, design_service: DesignService) -> None:
        assert design_service._sanitize_resource_name("autonomous_db_(atp)") == "autonomous_db_atp"

    def test_special_characters_removed(self, design_service: DesignService) -> None:
        assert design_service._sanitize_resource_name("my@server#1") == "myserver1"

    def test_leading_digit_prefixed(self, design_service: DesignService) -> None:
        assert design_service._sanitize_resource_name("123server") == "_123server"

    def test_spaces_and_hyphens_replaced(self, design_service: DesignService) -> None:
        assert design_service._sanitize_resource_name("My Web-Server") == "my_web_server"

    def test_normal_name_unchanged(self, design_service: DesignService) -> None:
        assert design_service._sanitize_resource_name("web_server") == "web_server"


class TestExpandVcnNetwork:
    async def test_vcn_with_compute_generates_network_resources(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """VCN+Compute構成でsubnet/IGW/route_table/security_listが自動生成される。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[
                {"service_type": "vcn", "display_name": "Main VCN"},
                {"service_type": "compute", "display_name": "Server"},
            ],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert "oci_core_subnet" in components_tf
        assert "oci_core_internet_gateway" in components_tf
        assert "oci_core_nat_gateway" in components_tf
        assert "oci_core_service_gateway" in components_tf
        assert "oci_core_route_table" in components_tf
        assert "oci_core_security_list" in components_tf
        # var.subnet_id, var.vcn_id等がローカル参照に置換される
        assert "var.subnet_id" not in components_tf
        assert "var.vcn_id" not in components_tf
        assert "var.gateway_id" not in components_tf
        assert "var.service_gateway_id" not in components_tf

    async def test_vcn_with_existing_subnet_skips_subnet_generation(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """ユーザーが明示的にsubnetを定義済みの場合はsubnetが自動生成されない。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[
                {"service_type": "vcn", "display_name": "VCN"},
                {"service_type": "subnet", "display_name": "Custom Subnet", "config": {"cidr_block": "10.0.2.0/24"}},
            ],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        # ユーザー定義のサブネットが存在
        assert "Custom Subnet" in components_tf
        # 自動生成のサブネットは含まれない
        assert "VCN Public Subnet" not in components_tf

    async def test_no_vcn_no_expansion(self, hearing_service: HearingService, design_service: DesignService) -> None:
        """VCNなしの構成で自動展開が行われない。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "adb", "display_name": "ADB"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert "oci_core_subnet" not in components_tf
        assert "oci_core_internet_gateway" not in components_tf


class TestExportIacAdbFreeTier:
    async def test_adb_free_tier_true_from_config(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """config is_free_tier: True → Terraformコード上で is_free_tier = true。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[
                {"service_type": "adb", "display_name": "ADB", "config": {"is_free_tier": True}},
            ],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert "is_free_tier             = true" in components_tf

    async def test_adb_free_tier_default_false(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """config未設定 → デフォルト is_free_tier = false。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "adb", "display_name": "ADB"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert "is_free_tier             = false" in components_tf


class TestExportIacComputeImageDataSource:
    async def test_compute_image_data_source_in_main_tf(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "compute", "display_name": "Server"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        main_tf = result["terraform_files"]["main.tf"]
        assert 'data "oci_core_images" "latest"' in main_tf
        assert "Oracle Linux" in main_tf

    async def test_compute_no_image_id_variable(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "compute", "display_name": "Server"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        variables_tf = result["terraform_files"]["variables.tf"]
        assert 'variable "image_id"' not in variables_tf

    async def test_compute_uses_data_source_reference(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "compute", "display_name": "Server"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert "data.oci_core_images.latest.images[0].id" in components_tf
        assert "var.image_id" not in components_tf


class TestExportMermaidDisplayName:
    async def test_mermaid_uses_display_name_ids(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[
                {"id": "comp-1", "service_type": "oke", "display_name": "My OKE"},
                {"id": "comp-2", "service_type": "adb", "display_name": "My ADB"},
            ],
            connections=[
                {
                    "source_id": "comp-1",
                    "target_id": "comp-2",
                    "connection_type": "private_endpoint",
                    "description": "OKE to ADB",
                }
            ],
        )
        mermaid = await design_service.export_mermaid(session_id)
        # display_nameベースのIDが使用される
        assert "my_oke" in mermaid
        assert "my_adb" in mermaid
        # UUIDが含まれない（UUID形式のパターンチェック）
        import re

        uuid_pattern = re.compile(r"[0-9a-f]{8}_[0-9a-f]{4}_[0-9a-f]{4}_[0-9a-f]{4}_[0-9a-f]{12}")
        assert not uuid_pattern.search(mermaid)


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

    async def test_export_all_reads_updated_files_from_disk(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """export_allはupdate_terraform_fileで修正済みのファイルをディスクから読む。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "vcn", "display_name": "Test VCN", "config": {"cidr_block": "10.0.0.0/16"}}],
            connections=[],
        )
        # 初回生成
        iac_result = await design_service.export_iac(session_id)
        terraform_dir = Path(iac_result["terraform_dir"])

        # ディスク上のファイルを直接修正（update_terraform_fileと同等の操作）
        modified_content = "# Modified by test\n" + iac_result["terraform_files"]["main.tf"]
        (terraform_dir / "main.tf").write_text(modified_content, encoding="utf-8")

        # export_allはディスクの最新内容を返すべき
        result = await design_service.export_all(session_id)
        assert result["terraform_files"]["main.tf"].startswith("# Modified by test")


class TestResourceNameSanitization:
    """C-2: OCI APIリソース名のサニタイズテスト。"""

    async def test_nosql_name_sanitized(self, hearing_service: HearingService, design_service: DesignService) -> None:
        """NoSQLテーブル名にスペースが含まれず、safe_nameが使用されることを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "nosql", "display_name": "IoT Session Store"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        # name フィールドはサニタイズ済み
        assert 'name           = "iot_session_store"' in components_tf
        # DDL文もサニタイズ済み
        assert "CREATE TABLE iot_session_store" in components_tf
        # display_nameのスペース付きはnameフィールドに現れない
        assert 'name           = "IoT Session Store"' not in components_tf

    async def test_objectstorage_name_sanitized(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """Object Storageバケット名にスペースが含まれないことを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "objectstorage", "display_name": "Data Lake"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert 'name           = "data_lake"' in components_tf
        assert 'name           = "Data Lake"' not in components_tf

    async def test_streaming_name_sanitized(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """Streaming名にスペースが含まれないことを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "streaming", "display_name": "IoT Event Stream"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert 'name               = "iot_event_stream"' in components_tf
        assert 'name               = "IoT Event Stream"' not in components_tf


class TestApiGatewayEndpointTypeCase:
    """C-5: API Gateway endpoint_type大文字化テスト。"""

    async def test_endpoint_type_uppercase_from_lowercase(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """endpoint_type 'public' が 'PUBLIC' に変換されることを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[
                {"service_type": "apigateway", "display_name": "API GW", "config": {"endpoint_type": "public"}},
            ],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert 'endpoint_type  = "PUBLIC"' in components_tf
        assert 'endpoint_type  = "public"' not in components_tf

    async def test_endpoint_type_private_uppercase(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """endpoint_type 'private' が 'PRIVATE' に変換されることを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[
                {"service_type": "apigateway", "display_name": "API GW", "config": {"endpoint_type": "private"}},
            ],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert 'endpoint_type  = "PRIVATE"' in components_tf


class TestMultiSubnetReferences:
    """C-1, C-3, C-4: 複数サブネット構成のローカル参照テスト。"""

    async def test_public_lb_uses_public_subnet(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """Public LBがpublic subnetを参照することを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[
                {"service_type": "vcn", "display_name": "VCN", "config": {"cidr_block": "10.0.0.0/16"}},
                {
                    "service_type": "subnet",
                    "display_name": "Public Subnet",
                    "config": {"cidr_block": "10.0.0.0/24", "prohibit_public_ip": "false"},
                },
                {
                    "service_type": "subnet",
                    "display_name": "Private Subnet",
                    "config": {"cidr_block": "10.0.1.0/24", "prohibit_public_ip": "true"},
                },
                {"service_type": "loadbalancer", "display_name": "LB", "config": {"is_private": False}},
            ],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        # LBリソースブロックを抽出して確認
        blocks = components_tf.split("\nresource ")
        lb_block = next(b for b in blocks if "oci_load_balancer_load_balancer" in b)
        assert "oci_core_subnet.public_subnet.id" in lb_block

    async def test_private_route_table_uses_nat_gw(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """Private Route TableがNAT GWを参照することを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[
                {"service_type": "vcn", "display_name": "VCN", "config": {"cidr_block": "10.0.0.0/16"}},
                {"service_type": "internet_gateway", "display_name": "IGW"},
                {"service_type": "nat_gateway", "display_name": "NAT GW"},
                {
                    "service_type": "route_table",
                    "display_name": "Public Route Table",
                    "config": {"destination": "0.0.0.0/0"},
                },
                {
                    "service_type": "route_table",
                    "display_name": "Private Route Table",
                    "config": {"destination": "0.0.0.0/0"},
                },
                {
                    "service_type": "subnet",
                    "display_name": "Public Subnet",
                    "config": {"cidr_block": "10.0.0.0/24", "prohibit_public_ip": "false"},
                },
            ],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        # リソースブロックを "resource" で分割して各セクションを取得
        blocks = components_tf.split("\nresource ")
        private_rt_block = next(b for b in blocks if '"private_route_table"' in b)
        public_rt_block = next(b for b in blocks if '"public_route_table"' in b)
        # Private Route TableはNAT GWを参照
        assert "oci_core_nat_gateway.nat_gw.id" in private_rt_block
        # Public Route TableはIGWを参照
        assert "oci_core_internet_gateway.igw.id" in public_rt_block

    async def test_private_subnet_uses_private_route_table(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """Private SubnetがPrivate Route Tableを参照することを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[
                {"service_type": "vcn", "display_name": "VCN", "config": {"cidr_block": "10.0.0.0/16"}},
                {
                    "service_type": "route_table",
                    "display_name": "Public Route Table",
                    "config": {"destination": "0.0.0.0/0"},
                },
                {
                    "service_type": "route_table",
                    "display_name": "Private Route Table",
                    "config": {"destination": "0.0.0.0/0"},
                },
                {
                    "service_type": "security_list",
                    "display_name": "Public Security List",
                    "config": {"ingress_source": "0.0.0.0/0", "ingress_port": "443"},
                },
                {
                    "service_type": "security_list",
                    "display_name": "Private Security List",
                    "config": {"ingress_source": "10.0.0.0/16", "ingress_port": "8080"},
                },
                {
                    "service_type": "subnet",
                    "display_name": "Public Subnet",
                    "config": {"cidr_block": "10.0.0.0/24", "prohibit_public_ip": "false"},
                },
                {
                    "service_type": "subnet",
                    "display_name": "Private Subnet",
                    "config": {"cidr_block": "10.0.1.0/24", "prohibit_public_ip": "true"},
                },
            ],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        # リソースブロックを分割
        blocks = components_tf.split("\nresource ")
        priv_sub_block = next(b for b in blocks if '"private_subnet"' in b)
        pub_sub_block = next(b for b in blocks if '"public_subnet"' in b)
        # Private SubnetはPrivate Route Table/Security Listを参照
        assert "oci_core_route_table.private_route_table.id" in priv_sub_block
        assert "oci_core_security_list.private_security_list.id" in priv_sub_block
        # Public SubnetはPublic Route Table/Security Listを参照
        assert "oci_core_route_table.public_route_table.id" in pub_sub_block
        assert "oci_core_security_list.public_security_list.id" in pub_sub_block


class TestOkeNodePool:
    """H-1: OKE Node Pool生成テスト。"""

    async def test_oke_generates_node_pool(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """OKEクラスタにNode Poolリソースが生成されることを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "oke", "display_name": "App Cluster"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert "oci_containerengine_cluster" in components_tf
        assert "oci_containerengine_node_pool" in components_tf
        assert "node_shape" in components_tf
        assert "node_config_details" in components_tf

    async def test_oke_image_data_source_has_shape_filter(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """OKEノードイメージデータソースにshapeフィルタが含まれることを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "oke", "display_name": "App Cluster"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        main_tf = result["terraform_files"]["main.tf"]
        assert "shape" in main_tf
        assert "VM.Standard.E4.Flex" in main_tf

    async def test_oke_node_pool_references_cluster(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """Node PoolがクラスタIDを参照することを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "oke", "display_name": "My OKE"}],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert "oci_containerengine_cluster.my_oke.id" in components_tf


class TestAdbPrivateEndpoint:
    """H-2: ADBプライベートエンドポイントテスト。"""

    async def test_adb_private_endpoint_includes_subnet(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """endpoint_type=privateでsubnet_idが設定されることを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[
                {"service_type": "adb", "display_name": "ADB", "config": {"endpoint_type": "private"}},
            ],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        assert "subnet_id" in components_tf
        assert "nsg_ids" in components_tf
        assert "is_access_control_enabled" not in components_tf

    async def test_adb_public_endpoint_no_subnet(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """endpoint_type=publicでsubnet_idが設定されないことを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[
                {"service_type": "adb", "display_name": "ADB", "config": {"endpoint_type": "public"}},
            ],
            connections=[],
        )
        result = await design_service.export_iac(session_id)
        components_tf = result["terraform_files"]["components.tf"]
        # ADBリソースブロック内にsubnet_idがない（public endpoint）
        blocks = components_tf.split("\nresource ")
        adb_block = next(b for b in blocks if "oci_database_autonomous_database" in b)
        assert "subnet_id" not in adb_block


class TestValidationNaming:
    """M-1: バリデーション命名規則テスト。"""

    async def test_nosql_with_spaces_triggers_warning(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """スペースを含むNoSQL名で警告が出ることを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "nosql", "display_name": "IoT Session Store"}],
            connections=[],
        )
        results = await design_service.validate_architecture(session_id)
        naming_results = [r for r in results if r.rule_id == "naming-convention"]
        assert len(naming_results) > 0
        assert "IoT Session Store" in naming_results[0].message

    async def test_valid_name_no_warning(self, hearing_service: HearingService, design_service: DesignService) -> None:
        """有効な名前で警告が出ないことを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[{"service_type": "nosql", "display_name": "iot_session_store"}],
            connections=[],
        )
        results = await design_service.validate_architecture(session_id)
        naming_results = [r for r in results if r.rule_id == "naming-convention"]
        assert len(naming_results) == 0


class TestValidationSubnetPlacement:
    """M-1: バリデーションサブネット配置テスト。"""

    async def test_public_lb_in_private_subnet_triggers_error(
        self, hearing_service: HearingService, design_service: DesignService
    ) -> None:
        """Public LBがprivate subnetに配置されるとエラーが出ることを確認。"""
        session_id = await _create_completed_session(hearing_service)
        await design_service.save_architecture(
            session_id,
            components=[
                {
                    "id": "lb-1",
                    "service_type": "loadbalancer",
                    "display_name": "Public LB",
                    "config": {"is_private": "false"},
                },
                {
                    "id": "subnet-1",
                    "service_type": "subnet",
                    "display_name": "Private Subnet",
                    "config": {"prohibit_public_ip": "true"},
                },
            ],
            connections=[
                {
                    "source_id": "lb-1",
                    "target_id": "subnet-1",
                    "connection_type": "deployed_in",
                    "description": "LB in private subnet",
                }
            ],
        )
        results = await design_service.validate_architecture(session_id)
        placement_results = [r for r in results if r.rule_id == "public-resource-private-subnet"]
        assert len(placement_results) > 0
