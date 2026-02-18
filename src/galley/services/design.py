"""アーキテクチャ設計の管理とバリデーションを行うサービス。"""

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

        parsed_components = [Component.model_validate(c) for c in components]
        parsed_connections = [Connection.model_validate(c) for c in connections]

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

    async def export_iac(self, session_id: str) -> dict[str, str]:
        """IaCテンプレート（Terraform）を出力する。

        Args:
            session_id: セッションID。

        Returns:
            ファイル名→内容のマッピング。

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

        # variables.tf
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
        files["variables.tf"] = "\n".join(var_lines)

        # components.tf - コンポーネントごとのリソース定義スケルトン
        comp_lines: list[str] = []
        comp_lines.append("# Auto-generated Terraform resource definitions")
        comp_lines.append(f"# Architecture: {session_id}")
        comp_lines.append(f"# Components: {len(arch.components)}")
        comp_lines.append("")
        for comp in arch.components:
            safe_name = comp.display_name.replace(" ", "_").replace("-", "_").lower()
            comp_lines.append(f"# {comp.display_name} ({comp.service_type})")
            comp_lines.append(f"# TODO: Implement {comp.service_type} resource")
            comp_lines.append(f'# resource "oci_{comp.service_type}" "{safe_name}" {{')
            for key, value in comp.config.items():
                comp_lines.append(f"#   {key} = {repr(value)}")
            comp_lines.append("# }")
            comp_lines.append("")
        files["components.tf"] = "\n".join(comp_lines)

        return files

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
        terraform_files = await self.export_iac(session_id)

        return {
            "summary": summary,
            "mermaid": mermaid,
            "terraform_files": terraform_files,
        }
