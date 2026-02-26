"""アーキテクチャ設計の管理とバリデーションを行うサービス。"""

import json
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from galley.models.architecture import Architecture, Component, Connection
from galley.models.errors import (
    ArchitectureNotFoundError,
    ComponentNotFoundError,
    HearingNotCompletedError,
    StorageError,
)
from galley.models.validation import ValidationResult
from galley.storage.service import StorageService
from galley.validators.architecture import ArchitectureValidator

# サービスタイプ → Terraform リソース定義テンプレートのマッピング
_TF_RESOURCE_TEMPLATES: dict[str, str] = {
    "vcn": """resource "oci_core_vcn" "{name}" {{
  compartment_id = var.compartment_ocid
  cidr_blocks    = ["{cidr_block}"]
  display_name   = "{display_name}"
}}""",
    "compute": """resource "oci_core_instance" "{name}" {{
  compartment_id      = var.compartment_ocid
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  shape               = "{shape}"
  display_name        = "{display_name}"

  shape_config {{
    ocpus         = {ocpus}
    memory_in_gbs = {memory_in_gbs}
  }}

  source_details {{
    source_type = "image"
    source_id   = data.oci_core_images.latest.images[0].id
  }}

  create_vnic_details {{
    subnet_id = var.subnet_id
  }}
}}""",
    "oke": """resource "oci_containerengine_cluster" "{name}" {{
  compartment_id     = var.compartment_ocid
  kubernetes_version = "{kubernetes_version}"
  name               = "{display_name}"
  vcn_id             = var.vcn_id

  endpoint_config {{
    is_public_ip_enabled = true
    subnet_id            = var.subnet_id
  }}

  options {{
    service_lb_subnet_ids = [var.subnet_id]
  }}
}}

resource "oci_containerengine_node_pool" "{name}_node_pool" {{
  compartment_id     = var.compartment_ocid
  cluster_id         = oci_containerengine_cluster.{name}.id
  kubernetes_version = "{kubernetes_version}"
  name               = "{display_name}-node-pool"

  node_shape = "{node_shape}"
  node_shape_config {{
    ocpus         = {node_ocpus}
    memory_in_gbs = {node_memory}
  }}

  node_config_details {{
    size = {node_count}

    placement_configs {{
      availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
      subnet_id           = var.node_subnet_id
    }}
  }}

  node_source_details {{
    source_type = "IMAGE"
    image_id    = data.oci_core_images.oke_node.images[0].id
  }}
}}""",
    "adb": """resource "oci_database_autonomous_database" "{name}" {{
  compartment_id           = var.compartment_ocid
  db_name                  = "{db_name}"
  display_name             = "{display_name}"
  cpu_core_count           = {cpu_core_count}
  data_storage_size_in_tbs = {storage_in_tbs}
  db_workload              = "{workload_type}"
  is_free_tier             = {is_free_tier}
  admin_password           = var.adb_admin_password
{adb_private_endpoint_block}}}""",
    "apigateway": """resource "oci_apigateway_gateway" "{name}" {{
  compartment_id = var.compartment_ocid
  endpoint_type  = "{endpoint_type}"
  subnet_id      = var.subnet_id
  display_name   = "{display_name}"
}}""",
    "functions": """resource "oci_functions_application" "{name}_app" {{
  compartment_id = var.compartment_ocid
  display_name   = "{display_name}"
  subnet_ids     = [var.subnet_id]
}}

resource "oci_functions_function" "{name}" {{
  application_id = oci_functions_application.{name}_app.id
  display_name   = "{display_name}"
  memory_in_mbs  = {memory_in_mbs}
  image          = var.function_image
}}""",
    "objectstorage": """resource "oci_objectstorage_bucket" "{name}" {{
  compartment_id = var.compartment_ocid
  namespace      = var.object_storage_namespace
  name           = "{safe_name}"
  storage_tier   = "{storage_tier}"
  versioning     = "{versioning}"
}}""",
    "loadbalancer": """resource "oci_load_balancer_load_balancer" "{name}" {{
  compartment_id = var.compartment_ocid
  display_name   = "{display_name}"
  shape          = "{shape}"
  subnet_ids     = [var.subnet_id]
  is_private     = {is_private}

  shape_details {{
    minimum_bandwidth_in_mbps = {min_bandwidth}
    maximum_bandwidth_in_mbps = {max_bandwidth}
  }}
}}""",
    "streaming": """resource "oci_streaming_stream" "{name}" {{
  compartment_id     = var.compartment_ocid
  name               = "{safe_name}"
  partitions         = {partitions}
  retention_in_hours = {retention_in_hours}
}}""",
    "nosql": """resource "oci_nosql_table" "{name}" {{
  compartment_id = var.compartment_ocid
  name           = "{safe_name}"
  ddl_statement  = "CREATE TABLE {safe_name} (id STRING, data JSON, PRIMARY KEY(id))"

  table_limits {{
    max_read_units     = 50
    max_write_units    = 50
    max_storage_in_gbs = 25
  }}
}}""",
    "subnet": """resource "oci_core_subnet" "{name}" {{
  compartment_id    = var.compartment_ocid
  vcn_id            = var.vcn_id
  cidr_block        = "{cidr_block}"
  display_name      = "{display_name}"
  prohibit_public_ip_on_vnic = {prohibit_public_ip}
  route_table_id    = var.route_table_id
  security_list_ids = [var.security_list_id]
}}""",
    "internet_gateway": """resource "oci_core_internet_gateway" "{name}" {{
  compartment_id = var.compartment_ocid
  vcn_id         = var.vcn_id
  display_name   = "{display_name}"
  enabled        = true
}}""",
    "nat_gateway": """resource "oci_core_nat_gateway" "{name}" {{
  compartment_id = var.compartment_ocid
  vcn_id         = var.vcn_id
  display_name   = "{display_name}"
}}""",
    "service_gateway": """resource "oci_core_service_gateway" "{name}" {{
  compartment_id = var.compartment_ocid
  vcn_id         = var.vcn_id
  display_name   = "{display_name}"

  services {{
    service_id = data.oci_core_services.all_services.services[0].id
  }}
}}""",
    "route_table": """resource "oci_core_route_table" "{name}" {{
  compartment_id = var.compartment_ocid
  vcn_id         = var.vcn_id
  display_name   = "{display_name}"

  route_rules {{
    network_entity_id = var.gateway_id
    destination       = "{destination}"
    destination_type  = "CIDR_BLOCK"
  }}
{sgw_route_block}}}""",
    "security_list": """resource "oci_core_security_list" "{name}" {{
  compartment_id = var.compartment_ocid
  vcn_id         = var.vcn_id
  display_name   = "{display_name}"

  egress_security_rules {{
    protocol    = "all"
    destination = "0.0.0.0/0"
  }}

  ingress_security_rules {{
    protocol = "6"
    source   = "{ingress_source}"

    tcp_options {{
      min = {ingress_port}
      max = {ingress_port}
    }}
  }}
}}""",
}

# サービスタイプ → 必要な追加Terraform変数のマッピング
_TF_REQUIRED_VARS: dict[str, list[dict[str, str]]] = {
    "compute": [
        {"name": "subnet_id", "description": "Subnet OCID", "type": "string"},
    ],
    "oke": [
        {"name": "vcn_id", "description": "VCN OCID", "type": "string"},
        {"name": "subnet_id", "description": "Subnet OCID (API endpoint)", "type": "string"},
        {"name": "node_subnet_id", "description": "Node pool subnet OCID", "type": "string"},
    ],
    "adb": [
        {"name": "adb_admin_password", "description": "ADB admin password", "type": "string", "sensitive": "true"},
        {"name": "subnet_id", "description": "Subnet OCID", "type": "string"},
    ],
    "apigateway": [
        {"name": "subnet_id", "description": "Subnet OCID", "type": "string"},
    ],
    "functions": [
        {"name": "subnet_id", "description": "Subnet OCID", "type": "string"},
        {"name": "function_image", "description": "Function container image URI", "type": "string"},
    ],
    "loadbalancer": [
        {"name": "subnet_id", "description": "Subnet OCID", "type": "string"},
    ],
    "objectstorage": [
        {"name": "object_storage_namespace", "description": "Object Storage namespace", "type": "string"},
    ],
    "subnet": [
        {"name": "vcn_id", "description": "VCN OCID", "type": "string"},
        {"name": "route_table_id", "description": "Route Table OCID", "type": "string"},
        {"name": "security_list_id", "description": "Security List OCID", "type": "string"},
    ],
    "internet_gateway": [
        {"name": "vcn_id", "description": "VCN OCID", "type": "string"},
    ],
    "nat_gateway": [
        {"name": "vcn_id", "description": "VCN OCID", "type": "string"},
    ],
    "service_gateway": [
        {"name": "vcn_id", "description": "VCN OCID", "type": "string"},
    ],
    "route_table": [
        {"name": "vcn_id", "description": "VCN OCID", "type": "string"},
        {"name": "gateway_id", "description": "Gateway OCID for route rule", "type": "string"},
        {"name": "service_gateway_id", "description": "Service Gateway OCID", "type": "string"},
    ],
    "security_list": [
        {"name": "vcn_id", "description": "VCN OCID", "type": "string"},
    ],
}

# サービスタイプ → 必要なTerraform data sourceブロックのマッピング
_TF_REQUIRED_DATA_SOURCES: dict[str, list[str]] = {
    "compute": [
        'data "oci_identity_availability_domains" "ads" {\n  compartment_id = var.compartment_ocid\n}',
        (
            'data "oci_core_images" "latest" {\n'
            "  compartment_id           = var.compartment_ocid\n"
            '  operating_system         = "Oracle Linux"\n'
            '  operating_system_version = "8"\n'
            '  sort_by                  = "TIMECREATED"\n'
            '  sort_order               = "DESC"\n'
            "}"
        ),
    ],
    "oke": [
        'data "oci_identity_availability_domains" "ads" {\n  compartment_id = var.compartment_ocid\n}',
        (
            'data "oci_core_images" "oke_node" {\n'
            "  compartment_id           = var.compartment_ocid\n"
            '  operating_system         = "Oracle Linux"\n'
            '  operating_system_version = "8"\n'
            '  shape                    = "VM.Standard.E4.Flex"\n'
            '  sort_by                  = "TIMECREATED"\n'
            '  sort_order               = "DESC"\n'
            "}"
        ),
    ],
    "service_gateway": [
        (
            'data "oci_core_services" "all_services" {\n'
            "  filter {\n"
            '    name   = "name"\n'
            '    values = ["All .* Services In Oracle Services Network"]\n'
            "    regex  = true\n"
            "  }\n"
            "}"
        ),
    ],
}

# ADB workload_type: ユーザー入力値 → OCI API値のマッピング
_ADB_WORKLOAD_MAP: dict[str, str] = {
    "ATP": "OLTP",
    "ADW": "DW",
}

# サービスタイプごとのデフォルト設定値
_TF_DEFAULTS: dict[str, dict[str, str]] = {
    "vcn": {"cidr_block": "10.0.0.0/16"},
    "compute": {"shape": "VM.Standard.E4.Flex", "ocpus": "1", "memory_in_gbs": "16"},
    "oke": {
        "kubernetes_version": "v1.31.1",
        "node_shape": "VM.Standard.E4.Flex",
        "node_ocpus": "1",
        "node_memory": "16",
        "node_count": "3",
    },
    "adb": {
        "db_name": "galleydb",
        "cpu_core_count": "1",
        "storage_in_tbs": "1",
        "workload_type": "OLTP",
        "is_free_tier": "false",
    },
    "apigateway": {"endpoint_type": "PUBLIC"},
    "functions": {"memory_in_mbs": "256"},
    "objectstorage": {"storage_tier": "Standard", "versioning": "Disabled"},
    "loadbalancer": {"shape": "flexible", "is_private": "false", "min_bandwidth": "10", "max_bandwidth": "100"},
    "streaming": {"partitions": "1", "retention_in_hours": "24"},
    "nosql": {},
    "subnet": {"cidr_block": "10.0.1.0/24", "prohibit_public_ip": "false"},
    "internet_gateway": {},
    "nat_gateway": {},
    "service_gateway": {},
    "route_table": {"destination": "0.0.0.0/0", "sgw_route_block": ""},
    "security_list": {"ingress_source": "0.0.0.0/0", "ingress_port": "22"},
}


class DesignService:
    """アーキテクチャ設計の管理とバリデーションを行う。"""

    def __init__(self, storage: StorageService, config_dir: Path) -> None:
        self._storage = storage
        self._config_dir = config_dir
        self._validator = ArchitectureValidator(config_dir=config_dir)
        self._services_cache: list[dict[str, Any]] | None = None

    def _load_services(self) -> list[dict[str, Any]]:
        """OCIサービス定義を読み込む。"""
        if self._services_cache is not None:
            return self._services_cache

        services_file = self._config_dir / "oci-services.yaml"
        try:
            with open(services_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            raise StorageError(f"サービス定義ファイルが見つかりません: {services_file}") from None
        self._services_cache = data["services"]
        return self._services_cache

    async def save_architecture(
        self,
        session_id: str,
        components: list[dict[str, Any]],
        connections: list[dict[str, Any]],
    ) -> Architecture:
        """アーキテクチャをセッションに保存する。

        Args:
            session_id: セッションID。
            components: コンポーネントリスト。
            connections: 接続リスト。

        Returns:
            保存されたアーキテクチャ。

        Raises:
            SessionNotFoundError: セッションが存在しない場合。
            HearingNotCompletedError: ヒアリングが未完了の場合。
        """
        session = await self._storage.load_session(session_id)
        if session.hearing_result is None:
            raise HearingNotCompletedError(session_id)

        # コンポーネントをパースし、仮ID→UUIDのマッピングを構築
        id_mapping: dict[str, str] = {}
        parsed_components: list[Component] = []
        for comp_data in components:
            original_id = comp_data.get("id", "")
            is_temp_id = bool(original_id) and not self._is_uuid(original_id)
            if is_temp_id:
                # 仮IDの場合: idフィールドを除外してパース（新しいUUIDを生成させる）
                comp_without_id = {k: v for k, v in comp_data.items() if k != "id"}
                parsed = Component.model_validate(comp_without_id)
                id_mapping[original_id] = parsed.id
            else:
                parsed = Component.model_validate(comp_data)
            parsed_components.append(parsed)

        # connectionsのsource_id/target_idを実UUIDに変換
        resolved_connections: list[dict[str, Any]] = []
        for conn_data in connections:
            resolved = dict(conn_data)
            resolved["source_id"] = id_mapping.get(resolved["source_id"], resolved["source_id"])
            resolved["target_id"] = id_mapping.get(resolved["target_id"], resolved["target_id"])
            resolved_connections.append(resolved)
        parsed_connections = [Connection.model_validate(c) for c in resolved_connections]

        architecture = Architecture(
            session_id=session_id,
            components=parsed_components,
            connections=parsed_connections,
        )
        session.architecture = architecture
        session.updated_at = datetime.now(UTC)
        await self._storage.save_session(session)
        return architecture

    async def add_component(
        self,
        session_id: str,
        service_type: str,
        display_name: str,
        config: dict[str, Any] | None = None,
    ) -> Component:
        """アーキテクチャにコンポーネントを追加する。

        Args:
            session_id: セッションID。
            service_type: OCIサービス種別。
            display_name: 表示名。
            config: サービス固有の設定。

        Returns:
            追加されたコンポーネント。

        Raises:
            SessionNotFoundError: セッションが存在しない場合。
            HearingNotCompletedError: ヒアリングが未完了の場合。
        """
        session = await self._storage.load_session(session_id)
        if session.hearing_result is None:
            raise HearingNotCompletedError(session_id)

        if session.architecture is None:
            session.architecture = Architecture(session_id=session_id)

        component = Component(
            id=str(uuid.uuid4()),
            service_type=service_type,
            display_name=display_name,
            config=config or {},
        )
        session.architecture.components.append(component)
        session.architecture.updated_at = datetime.now(UTC)
        session.updated_at = datetime.now(UTC)
        await self._storage.save_session(session)
        return component

    async def remove_component(self, session_id: str, component_id: str) -> None:
        """アーキテクチャからコンポーネントを削除する。

        関連する接続も同時に削除される。

        Args:
            session_id: セッションID。
            component_id: 削除するコンポーネントID。

        Raises:
            SessionNotFoundError: セッションが存在しない場合。
            ArchitectureNotFoundError: アーキテクチャが未設定の場合。
            ComponentNotFoundError: コンポーネントが見つからない場合。
        """
        session = await self._storage.load_session(session_id)
        if session.architecture is None:
            raise ArchitectureNotFoundError(session_id)

        arch = session.architecture
        original_count = len(arch.components)
        arch.components = [c for c in arch.components if c.id != component_id]

        if len(arch.components) == original_count:
            raise ComponentNotFoundError(component_id)

        # 関連する接続を削除
        arch.connections = [
            conn for conn in arch.connections if conn.source_id != component_id and conn.target_id != component_id
        ]

        arch.updated_at = datetime.now(UTC)
        session.updated_at = datetime.now(UTC)
        await self._storage.save_session(session)

    async def configure_component(
        self,
        session_id: str,
        component_id: str,
        config: dict[str, Any],
    ) -> Component:
        """コンポーネントの設定を変更する。

        Args:
            session_id: セッションID。
            component_id: 設定変更するコンポーネントID。
            config: 新しい設定値（既存設定とマージ）。

        Returns:
            更新されたコンポーネント。

        Raises:
            SessionNotFoundError: セッションが存在しない場合。
            ArchitectureNotFoundError: アーキテクチャが未設定の場合。
            ComponentNotFoundError: コンポーネントが見つからない場合。
        """
        session = await self._storage.load_session(session_id)
        if session.architecture is None:
            raise ArchitectureNotFoundError(session_id)

        for component in session.architecture.components:
            if component.id == component_id:
                component.config.update(config)
                session.architecture.updated_at = datetime.now(UTC)
                session.updated_at = datetime.now(UTC)
                await self._storage.save_session(session)
                return component

        raise ComponentNotFoundError(component_id)

    async def validate_architecture(self, session_id: str) -> list[ValidationResult]:
        """アーキテクチャをバリデーションルールに基づいて検証する。

        Args:
            session_id: セッションID。

        Returns:
            検出された問題のリスト。

        Raises:
            SessionNotFoundError: セッションが存在しない場合。
            ArchitectureNotFoundError: アーキテクチャが未設定の場合。
        """
        session = await self._storage.load_session(session_id)
        if session.architecture is None:
            raise ArchitectureNotFoundError(session_id)

        results = self._validator.validate(session.architecture)

        # 結果をアーキテクチャに保存
        session.architecture.validation_results = [r.model_dump() for r in results]
        session.architecture.updated_at = datetime.now(UTC)
        session.updated_at = datetime.now(UTC)
        await self._storage.save_session(session)

        return results

    async def list_available_services(self) -> list[dict[str, Any]]:
        """利用可能なOCIサービス一覧を返す。

        Returns:
            サービス定義のリスト。
        """
        return self._load_services()

    async def export_summary(self, session_id: str) -> str:
        """要件サマリーをMarkdown形式で出力する。

        Args:
            session_id: セッションID。

        Returns:
            Markdown形式のサマリー。

        Raises:
            SessionNotFoundError: セッションが存在しない場合。
            ArchitectureNotFoundError: アーキテクチャが未設定の場合。
        """
        session = await self._storage.load_session(session_id)
        if session.architecture is None:
            raise ArchitectureNotFoundError(session_id)

        arch = session.architecture
        lines: list[str] = []
        lines.append("# アーキテクチャサマリー")
        lines.append("")

        # ヒアリング結果がある場合はサマリーを含める
        if session.hearing_result is not None:
            lines.append("## 要件サマリー")
            lines.append("")
            lines.append(session.hearing_result.summary)
            lines.append("")

        lines.append("## コンポーネント一覧")
        lines.append("")
        lines.append("| コンポーネント | サービス種別 | 設定 |")
        lines.append("|---|---|---|")
        for comp in arch.components:
            config_str = ", ".join(f"{k}={v}" for k, v in comp.config.items()) if comp.config else "-"
            lines.append(f"| {comp.display_name} | {comp.service_type} | {config_str} |")
        lines.append("")

        if arch.connections:
            lines.append("## 接続関係")
            lines.append("")
            comp_map = {c.id: c.display_name for c in arch.components}
            for conn in arch.connections:
                source_name = comp_map.get(conn.source_id, conn.source_id)
                target_name = comp_map.get(conn.target_id, conn.target_id)
                lines.append(f"- {source_name} → {target_name} ({conn.connection_type}): {conn.description}")
            lines.append("")

        return "\n".join(lines)

    async def export_mermaid(self, session_id: str) -> str:
        """構成図をMermaid形式で出力する。

        Args:
            session_id: セッションID。

        Returns:
            Mermaid形式の構成図。

        Raises:
            SessionNotFoundError: セッションが存在しない場合。
            ArchitectureNotFoundError: アーキテクチャが未設定の場合。
        """
        session = await self._storage.load_session(session_id)
        if session.architecture is None:
            raise ArchitectureNotFoundError(session_id)

        arch = session.architecture
        lines: list[str] = []
        lines.append("graph TB")

        # コンポーネントID → display_nameベースの安全なIDマッピング
        id_to_safe: dict[str, str] = {}
        name_counts: dict[str, int] = {}
        for comp in arch.components:
            base_name = self._sanitize_resource_name(comp.display_name)
            count = name_counts.get(base_name, 0)
            name_counts[base_name] = count + 1
            safe_id = f"{base_name}_{count}" if count > 0 else base_name
            id_to_safe[comp.id] = safe_id

        # コンポーネントノード
        for comp in arch.components:
            safe_id = id_to_safe[comp.id]
            lines.append(f'    {safe_id}["{comp.display_name}<br/>({comp.service_type})"]')

        # 接続エッジ
        for conn in arch.connections:
            source_id = id_to_safe.get(conn.source_id, self._sanitize_resource_name(conn.source_id))
            target_id = id_to_safe.get(conn.target_id, self._sanitize_resource_name(conn.target_id))
            lines.append(f'    {source_id} -->|"{conn.connection_type}"| {target_id}')

        return "\n".join(lines)

    @staticmethod
    def _is_uuid(value: str) -> bool:
        """文字列がUUID形式かどうかを判定する。"""
        try:
            uuid.UUID(value)
            return True
        except ValueError:
            return False

    @staticmethod
    def _sanitize_resource_name(display_name: str) -> str:
        """display_nameをTerraform/Mermaid互換の安全な識別子に変換する。

        英数字・アンダースコア以外の文字を除去し、小文字に変換する。
        先頭が数字の場合はアンダースコアをプレフィックスする。
        """
        name = display_name.replace(" ", "_").replace("-", "_").lower()
        name = re.sub(r"[^a-z0-9_]", "", name)
        if name and name[0].isdigit():
            name = f"_{name}"
        if not name:
            name = "resource"
        return name

    def _format_hcl_value(self, value: Any) -> str:
        """Python値をHCL形式の文字列に変換する。"""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        return json.dumps(str(value))

    @staticmethod
    def _build_local_references(components: list[Component]) -> dict[str, str]:
        """アーキテクチャ内のコンポーネントからローカル参照マップを構築する。

        アーキテクチャにsubnetやvcnが含まれる場合、var.subnet_id/var.vcn_id を
        ローカルリソースへの参照に置換するためのマッピングを返す。

        Returns:
            "var." プレフィックスのキーはテンプレート変数に対応するデフォルト参照。
            "_" プレフィックスのキーはpublic/private解決用のコンテキスト情報。
        """
        refs: dict[str, str] = {}
        _safe = DesignService._sanitize_resource_name

        # VCN
        for comp in components:
            if comp.service_type == "vcn":
                refs["var.vcn_id"] = f"oci_core_vcn.{_safe(comp.display_name)}.id"
                break

        # Subnets: public/private分類
        public_subnet_ref: str | None = None
        private_subnet_ref: str | None = None
        for comp in components:
            if comp.service_type == "subnet":
                ref = f"oci_core_subnet.{_safe(comp.display_name)}.id"
                prohibit = str(comp.config.get("prohibit_public_ip", "false")).lower()
                if prohibit == "true":
                    if private_subnet_ref is None:
                        private_subnet_ref = ref
                else:
                    if public_subnet_ref is None:
                        public_subnet_ref = ref

        default_subnet = public_subnet_ref or private_subnet_ref
        if default_subnet:
            refs["var.subnet_id"] = default_subnet
        if private_subnet_ref:
            refs["_private_subnet_ref"] = private_subnet_ref

        # Internet Gateway / NAT Gateway / Service Gateway
        for comp in components:
            if comp.service_type == "internet_gateway":
                refs["_igw_ref"] = f"oci_core_internet_gateway.{_safe(comp.display_name)}.id"
            elif comp.service_type == "nat_gateway":
                refs["_nat_gw_ref"] = f"oci_core_nat_gateway.{_safe(comp.display_name)}.id"
            elif comp.service_type == "service_gateway":
                refs["var.service_gateway_id"] = f"oci_core_service_gateway.{_safe(comp.display_name)}.id"

        # デフォルトgateway: IGW（後方互換）
        if "_igw_ref" in refs:
            refs["var.gateway_id"] = refs["_igw_ref"]

        # Route Tables: public/private分類（名前ベース）
        public_rt_ref: str | None = None
        private_rt_ref: str | None = None
        for comp in components:
            if comp.service_type == "route_table":
                ref = f"oci_core_route_table.{_safe(comp.display_name)}.id"
                if "private" in comp.display_name.lower():
                    if private_rt_ref is None:
                        private_rt_ref = ref
                else:
                    if public_rt_ref is None:
                        public_rt_ref = ref

        default_rt = public_rt_ref or private_rt_ref
        if default_rt:
            refs["var.route_table_id"] = default_rt
        if private_rt_ref:
            refs["_private_route_table_ref"] = private_rt_ref

        # Security Lists: public/private分類（名前ベース）
        public_sl_ref: str | None = None
        private_sl_ref: str | None = None
        for comp in components:
            if comp.service_type == "security_list":
                ref = f"oci_core_security_list.{_safe(comp.display_name)}.id"
                if "private" in comp.display_name.lower():
                    if private_sl_ref is None:
                        private_sl_ref = ref
                else:
                    if public_sl_ref is None:
                        public_sl_ref = ref

        default_sl = public_sl_ref or private_sl_ref
        if default_sl:
            refs["var.security_list_id"] = default_sl
        if private_sl_ref:
            refs["_private_security_list_ref"] = private_sl_ref

        return refs

    @staticmethod
    def _get_component_refs(comp: Component, local_refs: dict[str, str]) -> dict[str, str]:
        """コンポーネント特性に基づいてローカル参照を選択的に解決する。

        テンプレート変数（var.*）のみを返し、コンポーネントのサービスタイプや
        設定に応じてpublic/privateリソースを適切に割り当てる。
        """
        # var.* キーのみ抽出（テンプレート変数に対応するもの）
        refs = {k: v for k, v in local_refs.items() if k.startswith("var.")}

        if comp.service_type == "subnet":
            # Private subnetにはprivate route table/security listを割り当て
            is_private = str(comp.config.get("prohibit_public_ip", "false")).lower() == "true"
            if is_private:
                if "_private_route_table_ref" in local_refs:
                    refs["var.route_table_id"] = local_refs["_private_route_table_ref"]
                if "_private_security_list_ref" in local_refs:
                    refs["var.security_list_id"] = local_refs["_private_security_list_ref"]

        elif comp.service_type == "route_table":
            # Private route tableにはNAT GW、public route tableにはIGWを割り当て
            is_private = "private" in comp.display_name.lower()
            if is_private and "_nat_gw_ref" in local_refs:
                refs["var.gateway_id"] = local_refs["_nat_gw_ref"]
            elif not is_private and "_igw_ref" in local_refs:
                refs["var.gateway_id"] = local_refs["_igw_ref"]

        elif comp.service_type in ("loadbalancer", "apigateway", "oke"):
            # Public/Private判定に基づくサブネット選択
            is_private_resource = False
            if comp.service_type == "loadbalancer":
                is_private_resource = str(comp.config.get("is_private", "false")).lower() == "true"
            elif comp.service_type == "apigateway":
                is_private_resource = comp.config.get("endpoint_type", "PUBLIC").upper() == "PRIVATE"
            elif comp.service_type == "oke" and "_private_subnet_ref" in local_refs:
                # OKE: endpointはpublic、node_poolはprivateサブネット
                refs["var.node_subnet_id"] = local_refs["_private_subnet_ref"]

            if is_private_resource and "_private_subnet_ref" in local_refs:
                refs["var.subnet_id"] = local_refs["_private_subnet_ref"]

        elif comp.service_type == "functions":
            # Functionsは通常private subnetに配置
            if "_private_subnet_ref" in local_refs:
                refs["var.subnet_id"] = local_refs["_private_subnet_ref"]

        elif comp.service_type == "adb":
            # ADB private endpointの場合はprivate subnetを使用
            endpoint = comp.config.get("endpoint_type", "public")
            if str(endpoint).lower() == "private" and "_private_subnet_ref" in local_refs:
                refs["var.subnet_id"] = local_refs["_private_subnet_ref"]

        return refs

    @staticmethod
    def _expand_vcn_network(components: list[Component]) -> list[Component]:
        """VCNコンポーネントがある場合、欠落しているネットワークリソースを自動補完する。

        public/private両方のサブネット・ルートテーブル・セキュリティリストを生成し、
        Service Gatewayも自動追加する。元のリストは変更せず、新しいリストを返す。
        """
        service_types = {c.service_type for c in components}
        if "vcn" not in service_types:
            return list(components)

        expanded = list(components)
        vcn_comp = next(c for c in components if c.service_type == "vcn")
        vcn_name = vcn_comp.display_name

        if "internet_gateway" not in service_types:
            expanded.append(
                Component(
                    id=str(uuid.uuid4()),
                    service_type="internet_gateway",
                    display_name=f"{vcn_name} IGW",
                    config={},
                )
            )

        if "nat_gateway" not in service_types:
            expanded.append(
                Component(
                    id=str(uuid.uuid4()),
                    service_type="nat_gateway",
                    display_name=f"{vcn_name} NAT GW",
                    config={},
                )
            )

        if "service_gateway" not in service_types:
            expanded.append(
                Component(
                    id=str(uuid.uuid4()),
                    service_type="service_gateway",
                    display_name=f"{vcn_name} Service GW",
                    config={},
                )
            )

        if "security_list" not in service_types:
            expanded.append(
                Component(
                    id=str(uuid.uuid4()),
                    service_type="security_list",
                    display_name=f"{vcn_name} Public Security List",
                    config={"ingress_source": "0.0.0.0/0", "ingress_port": "443"},
                )
            )
            expanded.append(
                Component(
                    id=str(uuid.uuid4()),
                    service_type="security_list",
                    display_name=f"{vcn_name} Private Security List",
                    config={"ingress_source": "10.0.0.0/16", "ingress_port": "8000"},
                )
            )

        # Private route tableにはService Gatewayルートを含める
        _sgw_route = (
            "\n  route_rules {\n"
            "    network_entity_id = var.service_gateway_id\n"
            "    destination       = data.oci_core_services.all_services.services[0].cidr_block\n"
            '    destination_type  = "SERVICE_CIDR_BLOCK"\n'
            "  }\n"
        )

        if "route_table" not in service_types:
            expanded.append(
                Component(
                    id=str(uuid.uuid4()),
                    service_type="route_table",
                    display_name=f"{vcn_name} Public Route Table",
                    config={"destination": "0.0.0.0/0", "sgw_route_block": ""},
                )
            )
            expanded.append(
                Component(
                    id=str(uuid.uuid4()),
                    service_type="route_table",
                    display_name=f"{vcn_name} Private Route Table",
                    config={"destination": "0.0.0.0/0", "sgw_route_block": _sgw_route},
                )
            )

        if "subnet" not in service_types:
            expanded.append(
                Component(
                    id=str(uuid.uuid4()),
                    service_type="subnet",
                    display_name=f"{vcn_name} Public Subnet",
                    config={"cidr_block": "10.0.1.0/24", "prohibit_public_ip": "false"},
                )
            )
            expanded.append(
                Component(
                    id=str(uuid.uuid4()),
                    service_type="subnet",
                    display_name=f"{vcn_name} Private Subnet",
                    config={"cidr_block": "10.0.2.0/24", "prohibit_public_ip": "true"},
                )
            )

        return expanded

    def _render_component_tf(self, comp: Component) -> str:
        """コンポーネントからTerraformリソース定義を生成する。"""
        service_type = comp.service_type
        safe_name = self._sanitize_resource_name(comp.display_name)

        template = _TF_RESOURCE_TEMPLATES.get(service_type)
        if template is None:
            # テンプレートがないサービスタイプはコメント付きプレースホルダー
            config_lines = "\n".join(f"  # {k} = {self._format_hcl_value(v)}" for k, v in comp.config.items())
            return (
                f"# {comp.display_name} ({service_type})\n"
                f'# TODO: No built-in template for service type "{service_type}"\n'
                f'# resource "oci_{service_type}" "{safe_name}" {{\n'
                f"#   compartment_id = var.compartment_ocid\n"
                f"{config_lines}\n"
                f"# }}"
            )

        # デフォルト値をマージしてテンプレートに渡すパラメータを構築
        defaults = dict(_TF_DEFAULTS.get(service_type, {}))
        params: dict[str, str] = {
            "name": safe_name,
            "safe_name": safe_name,
            "display_name": comp.display_name,
        }
        params.update(defaults)
        # コンポーネント設定でデフォルトを上書き（bool値はHCL形式に変換）
        for k, v in comp.config.items():
            if isinstance(v, bool):
                params[k] = "true" if v else "false"
            else:
                params[k] = str(v)

        # API Gateway: endpoint_type を大文字に変換（OCI APIが要求）
        if service_type == "apigateway" and "endpoint_type" in params:
            params["endpoint_type"] = params["endpoint_type"].upper()

        # ADB: ユーザー入力の workload_type を OCI API値に変換
        if service_type == "adb" and "workload_type" in params:
            params["workload_type"] = _ADB_WORKLOAD_MAP.get(params["workload_type"], params["workload_type"])

        # Security List: ポート番号の最低値ガード（0は無効）
        if service_type == "security_list":
            port = int(params.get("ingress_port", "22") or "22")
            if port <= 0:
                params["ingress_port"] = "22"

        # ADB: プライベートエンドポイント設定
        if service_type == "adb":
            endpoint = params.get("endpoint_type", "public").lower()
            if endpoint == "private":
                params["adb_private_endpoint_block"] = (
                    "  subnet_id              = var.subnet_id\n  nsg_ids               = []\n"
                )
            else:
                params["adb_private_endpoint_block"] = ""

        return template.format(**params)

    async def export_iac(self, session_id: str) -> dict[str, Any]:
        """IaCテンプレート（Terraform）を出力する。

        Terraformファイルを生成し、セッションのデータディレクトリに書き出す。

        Args:
            session_id: セッションID。

        Returns:
            terraform_files（ファイル名→内容）とterraform_dir（書き出し先パス）を含む辞書。

        Raises:
            SessionNotFoundError: セッションが存在しない場合。
            ArchitectureNotFoundError: アーキテクチャが未設定の場合。
        """
        session = await self._storage.load_session(session_id)
        if session.architecture is None:
            raise ArchitectureNotFoundError(session_id)

        arch = session.architecture
        files: dict[str, str] = {}

        # VCNネットワークリソースの自動展開（元のアーキテクチャは変更しない）
        expanded_components = self._expand_vcn_network(arch.components)

        # main.tf
        main_lines: list[str] = []
        main_lines.append("terraform {")
        main_lines.append("  required_providers {")
        main_lines.append("    oci = {")
        main_lines.append('      source  = "oracle/oci"')
        main_lines.append('      version = ">= 5.0"')
        main_lines.append("    }")
        main_lines.append("  }")
        main_lines.append("}")
        main_lines.append("")
        main_lines.append('provider "oci" {')
        main_lines.append("  region = var.region")
        main_lines.append("}")
        files["main.tf"] = "\n".join(main_lines)

        # variables.tf - 基本変数 + コンポーネントが必要とする追加変数
        var_lines: list[str] = []
        var_lines.append('variable "region" {')
        var_lines.append('  description = "OCI region"')
        var_lines.append("  type        = string")
        var_lines.append("}")
        var_lines.append("")
        var_lines.append('variable "compartment_ocid" {')
        var_lines.append('  description = "Compartment OCID"')
        var_lines.append("  type        = string")
        var_lines.append("}")
        var_lines.append("")
        var_lines.append('variable "tenancy_ocid" {')
        var_lines.append('  description = "Tenancy OCID"')
        var_lines.append("  type        = string")
        var_lines.append("}")

        # R4: ローカル参照マップ — 展開後のコンポーネントが提供する変数を特定
        local_refs = self._build_local_references(expanded_components)
        # ローカルで解決される変数名を収集（"var." プレフィックスのみ対象）
        locally_provided_vars: set[str] = set()
        for var_ref in local_refs:
            if var_ref.startswith("var."):
                # "var.subnet_id" → "subnet_id"
                locally_provided_vars.add(var_ref.split(".")[-1])

        # コンポーネントに応じた追加変数を収集（重複排除 + ローカル提供分を除外）
        seen_vars: set[str] = set()
        all_var_defs: list[dict[str, str]] = []
        for comp in expanded_components:
            for var_def in _TF_REQUIRED_VARS.get(comp.service_type, []):
                var_name = var_def["name"]
                if var_name not in seen_vars and var_name not in locally_provided_vars:
                    seen_vars.add(var_name)
                    all_var_defs.append(var_def)
                    var_lines.append("")
                    var_lines.append(f'variable "{var_name}" {{')
                    var_lines.append(f'  description = "{var_def["description"]}"')
                    var_lines.append(f"  type        = {var_def['type']}")
                    if var_def.get("sensitive") == "true":
                        var_lines.append("  sensitive   = true")
                    var_lines.append("}")

        files["variables.tf"] = "\n".join(var_lines)

        # コンポーネントに応じたdata sourceブロックをmain.tfに追加
        data_source_blocks: list[str] = []
        seen_data_sources: set[str] = set()
        for comp in expanded_components:
            for ds_block in _TF_REQUIRED_DATA_SOURCES.get(comp.service_type, []):
                if ds_block not in seen_data_sources:
                    seen_data_sources.add(ds_block)
                    data_source_blocks.append(ds_block)

        if data_source_blocks:
            files["main.tf"] += "\n\n" + "\n\n".join(data_source_blocks)

        # components.tf - コンポーネントごとのリソース定義（ローカル参照を適用）
        comp_lines: list[str] = []
        comp_lines.append("# Auto-generated Terraform resource definitions")
        comp_lines.append(f"# Architecture: {session_id}")
        comp_lines.append(f"# Components: {len(expanded_components)}")
        comp_lines.append("")
        for comp in expanded_components:
            rendered = self._render_component_tf(comp)
            # R4: ローカル参照置換（コンポーネント特性に基づくpublic/private振り分け）
            comp_refs = self._get_component_refs(comp, local_refs)
            for old_ref, new_ref in comp_refs.items():
                rendered = rendered.replace(old_ref, new_ref)
            comp_lines.append(rendered)
            comp_lines.append("")
        files["components.tf"] = "\n".join(comp_lines)

        # R3: terraform.tfvars.example 生成
        tfvars_lines: list[str] = []
        tfvars_lines.append("# Terraform variables example")
        tfvars_lines.append("# Copy this file to terraform.tfvars and fill in actual values.")
        tfvars_lines.append("")
        tfvars_lines.append('# OCI region (e.g., "ap-osaka-1", "us-ashburn-1")')
        tfvars_lines.append('region = "ap-osaka-1"')
        tfvars_lines.append("")
        tfvars_lines.append("# Compartment OCID (auto-populated by Resource Manager)")
        tfvars_lines.append('compartment_ocid = "ocid1.compartment.oc1..example"')
        for var_def in all_var_defs:
            tfvars_lines.append("")
            tfvars_lines.append(f"# {var_def['description']}")
            tfvars_lines.append(f'{var_def["name"]} = "ocid1.example"')
        files["terraform.tfvars.example"] = "\n".join(tfvars_lines)

        # セッションのデータディレクトリにファイルを書き出す
        terraform_dir = self._storage.get_session_dir(session_id) / "terraform"
        terraform_dir.mkdir(parents=True, exist_ok=True)
        for filename, content in files.items():
            (terraform_dir / filename).write_text(content, encoding="utf-8")

        return {"terraform_files": files, "terraform_dir": str(terraform_dir)}

    async def export_all(self, session_id: str) -> dict[str, Any]:
        """全成果物を一括出力する。

        terraform_dirに既存ファイルがある場合はディスクから読み込む（update_terraform_file
        での修正を反映するため）。存在しない場合はexport_iacで新規生成する。

        Args:
            session_id: セッションID。

        Returns:
            summary, mermaid, terraform_files を含む辞書。

        Raises:
            SessionNotFoundError: セッションが存在しない場合。
            ArchitectureNotFoundError: アーキテクチャが未設定の場合。
        """
        session = await self._storage.load_session(session_id)
        if session.architecture is None:
            raise ArchitectureNotFoundError(session_id)

        summary = await self.export_summary(session_id)
        mermaid = await self.export_mermaid(session_id)

        # terraform_dirに既存ファイルがあればディスクから読み込む
        terraform_dir = self._storage.get_session_dir(session_id) / "terraform"
        if terraform_dir.exists():
            files: dict[str, str] = {}
            for tf_file in sorted(terraform_dir.iterdir()):
                if tf_file.is_file():
                    files[tf_file.name] = tf_file.read_text(encoding="utf-8")
            if files:
                return {
                    "summary": summary,
                    "mermaid": mermaid,
                    "terraform_files": files,
                    "terraform_dir": str(terraform_dir),
                }

        # 既存ファイルがなければ新規生成
        iac_result = await self.export_iac(session_id)

        return {
            "summary": summary,
            "mermaid": mermaid,
            "terraform_files": iac_result["terraform_files"],
            "terraform_dir": iac_result["terraform_dir"],
        }
