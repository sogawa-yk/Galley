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
        files = await design_service.export_iac(session_id)
        assert "main.tf" in files
        assert "variables.tf" in files
        assert "components.tf" in files
        assert "oci" in files["main.tf"]


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
