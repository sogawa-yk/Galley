"""設計層のMCPツール定義。"""

from typing import Any

from fastmcp import FastMCP

from galley.models.errors import GalleyError
from galley.services.design import DesignService


def register_design_tools(mcp: FastMCP, design_service: DesignService) -> None:
    """設計関連のMCPツールを登録する。"""

    @mcp.tool()
    async def save_architecture(
        session_id: str,
        components: list[dict[str, Any]],
        connections: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """推奨アーキテクチャをセッションに保存する。

        ヒアリング結果を分析して生成したアーキテクチャを保存します。
        ヒアリング完了済みのセッションに対してのみ実行可能です。

        Args:
            session_id: セッションID。
            components: コンポーネントリスト。各要素は
                {"service_type": str, "display_name": str, "config": dict} 形式。
            connections: 接続リスト。各要素は
                {"source_id": str, "target_id": str, "connection_type": str, "description": str} 形式。
        """
        try:
            architecture = await design_service.save_architecture(session_id, components, connections)
            return {
                "session_id": architecture.session_id,
                "components": [c.model_dump() for c in architecture.components],
                "connections": [c.model_dump() for c in architecture.connections],
                "created_at": architecture.created_at.isoformat(),
            }
        except GalleyError as e:
            return {"error": type(e).__name__, "message": str(e)}

    @mcp.tool()
    async def add_component(
        session_id: str,
        service_type: str,
        display_name: str,
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """アーキテクチャにコンポーネントを追加する。

        ヒアリング完了済みのセッションに対して、OCIサービスコンポーネントを追加します。
        アーキテクチャが未作成の場合は自動的に作成されます。

        Args:
            session_id: セッションID。
            service_type: OCIサービス種別（例: "oke", "adb", "compute"）。
            display_name: コンポーネントの表示名。
            config: サービス固有の設定（任意）。
        """
        try:
            component = await design_service.add_component(session_id, service_type, display_name, config)
            return component.model_dump()
        except GalleyError as e:
            return {"error": type(e).__name__, "message": str(e)}

    @mcp.tool()
    async def remove_component(
        session_id: str,
        component_id: str,
    ) -> dict[str, Any]:
        """アーキテクチャからコンポーネントを削除する。

        指定されたコンポーネントと、そのコンポーネントに関連する接続を削除します。

        Args:
            session_id: セッションID。
            component_id: 削除するコンポーネントのID。
        """
        try:
            await design_service.remove_component(session_id, component_id)
            return {"success": True}
        except GalleyError as e:
            return {"error": type(e).__name__, "message": str(e)}

    @mcp.tool()
    async def configure_component(
        session_id: str,
        component_id: str,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """コンポーネントの設定を変更する。

        既存の設定にマージする形で設定を更新します。

        Args:
            session_id: セッションID。
            component_id: 設定変更するコンポーネントのID。
            config: 新しい設定値。既存設定とマージされます。
        """
        try:
            component = await design_service.configure_component(session_id, component_id, config)
            return component.model_dump()
        except GalleyError as e:
            return {"error": type(e).__name__, "message": str(e)}

    @mcp.tool()
    async def validate_architecture(session_id: str) -> dict[str, Any]:
        """アーキテクチャ構成をバリデーションルールに基づいて検証する。

        OCI固有の制約やベストプラクティスに基づいて構成を検証し、
        問題点と推奨事項のリストを返します。

        Args:
            session_id: セッションID。
        """
        try:
            results = await design_service.validate_architecture(session_id)
            error_count = sum(1 for r in results if r.severity == "error")
            warning_count = sum(1 for r in results if r.severity == "warning")
            return {
                "results": [r.model_dump() for r in results],
                "error_count": error_count,
                "warning_count": warning_count,
            }
        except GalleyError as e:
            return {"error": type(e).__name__, "message": str(e)}

    @mcp.tool()
    async def list_available_services() -> dict[str, Any]:
        """利用可能なOCIサービス一覧を取得する。

        アーキテクチャに追加可能なOCIサービスの一覧を返します。
        各サービスにはサービス種別、表示名、説明、設定スキーマが含まれます。
        """
        try:
            services = await design_service.list_available_services()
            return {"services": services}
        except GalleyError as e:
            return {"error": type(e).__name__, "message": str(e)}
