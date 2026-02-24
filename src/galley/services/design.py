"""アーキテクチャ設計の管理とバリデーションを行うサービス。"""

import json
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
  compartment_id = var.compartment_id
  cidr_blocks    = ["{cidr_block}"]
  display_name   = "{display_name}"
}}""",
    "compute": """resource "oci_core_instance" "{name}" {{
  compartment_id      = var.compartment_id
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  shape               = "{shape}"
  display_name        = "{display_name}"

  shape_config {{
    ocpus         = {ocpus}
    memory_in_gbs = {memory_in_gbs}
  }}

  source_details {{
    source_type = "image"
    source_id   = var.image_id
  }}

  create_vnic_details {{
    subnet_id = var.subnet_id
  }}
}}""",
    "oke": """resource "oci_containerengine_cluster" "{name}" {{
  compartment_id     = var.compartment_id
  kubernetes_version = "{kubernetes_version}"
  name               = "{display_name}"
  vcn_id             = var.vcn_id

  endpoint_config {{
    is_public_ip_enabled = true
    subnet_id            = var.subnet_id
  }}
}}""",
    "adb": """resource "oci_database_autonomous_database" "{name}" {{
  compartment_id           = var.compartment_id
  db_name                  = "{db_name}"
  display_name             = "{display_name}"
  cpu_core_count           = {cpu_core_count}
  data_storage_size_in_tbs = {storage_in_tbs}
  db_workload              = "{workload_type}"
  is_free_tier             = false
}}""",
    "apigateway": """resource "oci_apigateway_gateway" "{name}" {{
  compartment_id = var.compartment_id
  endpoint_type  = "{endpoint_type}"
  subnet_id      = var.subnet_id
  display_name   = "{display_name}"
}}""",
    "functions": """resource "oci_functions_application" "{name}_app" {{
  compartment_id = var.compartment_id
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
  compartment_id = var.compartment_id
  namespace      = var.object_storage_namespace
  name           = "{display_name}"
  storage_tier   = "{storage_tier}"
  versioning     = "{versioning}"
}}""",
    "loadbalancer": """resource "oci_load_balancer_load_balancer" "{name}" {{
  compartment_id = var.compartment_id
  display_name   = "{display_name}"
  shape          = "{shape}"
  subnet_ids     = [var.subnet_id]
  is_private     = {is_private}
}}""",
    "streaming": """resource "oci_streaming_stream" "{name}" {{
  compartment_id     = var.compartment_id
  name               = "{display_name}"
  partitions         = {partitions}
  retention_in_hours = {retention_in_hours}
}}""",
    "nosql": """resource "oci_nosql_table" "{name}" {{
  compartment_id = var.compartment_id
  name           = "{display_name}"
  ddl_statement  = "CREATE TABLE {display_name} (id STRING, data JSON, PRIMARY KEY(id))"

  table_limits {{
    max_read_units     = 50
    max_write_units    = 50
    max_storage_in_gbs = 25
  }}
}}""",
}

# サービスタイプ → 必要な追加Terraform変数のマッピング
_TF_REQUIRED_VARS: dict[str, list[dict[str, str]]] = {
    "compute": [
        {"name": "image_id", "description": "Compute instance image OCID", "type": "string"},
        {"name": "subnet_id", "description": "Subnet OCID", "type": "string"},
    ],
    "oke": [
        {"name": "vcn_id", "description": "VCN OCID", "type": "string"},
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
}

# サービスタイプ → 必要なTerraform data sourceブロックのマッピング
_TF_REQUIRED_DATA_SOURCES: dict[str, list[str]] = {
    "compute": [
        'data "oci_identity_availability_domains" "ads" {\n  compartment_id = var.compartment_id\n}',
    ],
}

# サービスタイプごとのデフォルト設定値
_TF_DEFAULTS: dict[str, dict[str, str]] = {
    "vcn": {"cidr_block": "10.0.0.0/16"},
    "compute": {"shape": "VM.Standard.E4.Flex", "ocpus": "1", "memory_in_gbs": "16"},
    "oke": {"kubernetes_version": "v1.28"},
    "adb": {"db_name": "galleydb", "cpu_core_count": "1", "storage_in_tbs": "1", "workload_type": "ATP"},
    "apigateway": {"endpoint_type": "PUBLIC"},
    "functions": {"memory_in_mbs": "256"},
    "objectstorage": {"storage_tier": "Standard", "versioning": "Disabled"},
    "loadbalancer": {"shape": "flexible", "is_private": "false"},
    "streaming": {"partitions": "1", "retention_in_hours": "24"},
    "nosql": {},
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

        # コンポーネントノード
        for comp in arch.components:
            safe_id = comp.id.replace("-", "_")
            lines.append(f'    {safe_id}["{comp.display_name}<br/>({comp.service_type})"]')

        # 接続エッジ
        for conn in arch.connections:
            source_id = conn.source_id.replace("-", "_")
            target_id = conn.target_id.replace("-", "_")
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

    def _format_hcl_value(self, value: Any) -> str:
        """Python値をHCL形式の文字列に変換する。"""
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        return json.dumps(str(value))

    def _render_component_tf(self, comp: Component) -> str:
        """コンポーネントからTerraformリソース定義を生成する。"""
        service_type = comp.service_type
        safe_name = comp.display_name.replace(" ", "_").replace("-", "_").lower()

        template = _TF_RESOURCE_TEMPLATES.get(service_type)
        if template is None:
            # テンプレートがないサービスタイプはコメント付きプレースホルダー
            config_lines = "\n".join(f"  # {k} = {self._format_hcl_value(v)}" for k, v in comp.config.items())
            return (
                f"# {comp.display_name} ({service_type})\n"
                f'# TODO: No built-in template for service type "{service_type}"\n'
                f'# resource "oci_{service_type}" "{safe_name}" {{\n'
                f"#   compartment_id = var.compartment_id\n"
                f"{config_lines}\n"
                f"# }}"
            )

        # デフォルト値をマージしてテンプレートに渡すパラメータを構築
        defaults = dict(_TF_DEFAULTS.get(service_type, {}))
        params: dict[str, str] = {
            "name": safe_name,
            "display_name": comp.display_name,
        }
        params.update(defaults)
        # コンポーネント設定でデフォルトを上書き
        for k, v in comp.config.items():
            params[k] = str(v)

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
        var_lines.append('variable "compartment_id" {')
        var_lines.append('  description = "Compartment OCID"')
        var_lines.append("  type        = string")
        var_lines.append("}")

        # コンポーネントに応じた追加変数を収集（重複排除）
        seen_vars: set[str] = set()
        for comp in arch.components:
            for var_def in _TF_REQUIRED_VARS.get(comp.service_type, []):
                var_name = var_def["name"]
                if var_name not in seen_vars:
                    seen_vars.add(var_name)
                    var_lines.append("")
                    var_lines.append(f'variable "{var_name}" {{')
                    var_lines.append(f'  description = "{var_def["description"]}"')
                    var_lines.append(f"  type        = {var_def['type']}")
                    var_lines.append("}")

        files["variables.tf"] = "\n".join(var_lines)

        # コンポーネントに応じたdata sourceブロックをmain.tfに追加
        data_source_blocks: list[str] = []
        seen_data_sources: set[str] = set()
        for comp in arch.components:
            for ds_block in _TF_REQUIRED_DATA_SOURCES.get(comp.service_type, []):
                if ds_block not in seen_data_sources:
                    seen_data_sources.add(ds_block)
                    data_source_blocks.append(ds_block)

        if data_source_blocks:
            files["main.tf"] += "\n\n" + "\n\n".join(data_source_blocks)

        # components.tf - コンポーネントごとのリソース定義
        comp_lines: list[str] = []
        comp_lines.append("# Auto-generated Terraform resource definitions")
        comp_lines.append(f"# Architecture: {session_id}")
        comp_lines.append(f"# Components: {len(arch.components)}")
        comp_lines.append("")
        for comp in arch.components:
            comp_lines.append(self._render_component_tf(comp))
            comp_lines.append("")
        files["components.tf"] = "\n".join(comp_lines)

        # セッションのデータディレクトリにファイルを書き出す
        terraform_dir = self._storage.get_session_dir(session_id) / "terraform"
        terraform_dir.mkdir(parents=True, exist_ok=True)
        for filename, content in files.items():
            (terraform_dir / filename).write_text(content, encoding="utf-8")

        return {"terraform_files": files, "terraform_dir": str(terraform_dir)}

    async def export_all(self, session_id: str) -> dict[str, Any]:
        """全成果物を一括出力する。

        Args:
            session_id: セッションID。

        Returns:
            summary, mermaid, terraform_files を含む辞書。

        Raises:
            SessionNotFoundError: セッションが存在しない場合。
            ArchitectureNotFoundError: アーキテクチャが未設定の場合。
        """
        summary = await self.export_summary(session_id)
        mermaid = await self.export_mermaid(session_id)
        iac_result = await self.export_iac(session_id)

        return {
            "summary": summary,
            "mermaid": mermaid,
            "terraform_files": iac_result["terraform_files"],
            "terraform_dir": iac_result["terraform_dir"],
        }
