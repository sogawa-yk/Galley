"""Architectureモデルのユニットテスト。"""

from galley.models.architecture import Architecture, Component, Connection


class TestComponent:
    def test_component_default_id(self) -> None:
        comp = Component(service_type="oke", display_name="OKEクラスター")
        assert comp.id is not None
        assert len(comp.id) > 0

    def test_component_custom_id(self) -> None:
        comp = Component(id="custom-id", service_type="oke", display_name="OKEクラスター")
        assert comp.id == "custom-id"

    def test_component_default_config(self) -> None:
        comp = Component(service_type="adb", display_name="ADB")
        assert comp.config == {}

    def test_component_with_config(self) -> None:
        comp = Component(
            service_type="adb",
            display_name="分析用ADB",
            config={"endpoint_type": "private", "cpu_core_count": 2},
        )
        assert comp.config["endpoint_type"] == "private"
        assert comp.config["cpu_core_count"] == 2

    def test_component_default_customizable(self) -> None:
        comp = Component(service_type="oke", display_name="OKE")
        assert comp.customizable is True


class TestConnection:
    def test_connection_creation(self) -> None:
        conn = Connection(
            source_id="src-id",
            target_id="tgt-id",
            connection_type="private_endpoint",
            description="OKE to ADB via Private Endpoint",
        )
        assert conn.source_id == "src-id"
        assert conn.target_id == "tgt-id"
        assert conn.connection_type == "private_endpoint"


class TestArchitecture:
    def test_architecture_creation(self) -> None:
        arch = Architecture(session_id="test-session")
        assert arch.session_id == "test-session"
        assert arch.components == []
        assert arch.connections == []
        assert arch.validation_results is None
        assert arch.created_at is not None
        assert arch.updated_at is not None

    def test_architecture_with_components(self) -> None:
        comp = Component(service_type="oke", display_name="OKE")
        arch = Architecture(session_id="test-session", components=[comp])
        assert len(arch.components) == 1
        assert arch.components[0].service_type == "oke"

    def test_architecture_serialization(self) -> None:
        comp = Component(service_type="oke", display_name="OKE", config={"node_count": 3})
        conn = Connection(
            source_id=comp.id,
            target_id="other-id",
            connection_type="public",
            description="test",
        )
        arch = Architecture(session_id="s1", components=[comp], connections=[conn])
        data = arch.model_dump()
        restored = Architecture.model_validate(data)
        assert restored.session_id == "s1"
        assert len(restored.components) == 1
        assert len(restored.connections) == 1
