"""アプリケーション層のMCPツール定義。"""

from typing import Any

from fastmcp import FastMCP

from galley.models.errors import GalleyError
from galley.services.app import AppService


def register_app_tools(mcp: FastMCP, app_service: AppService) -> None:
    """アプリケーション関連のMCPツールを登録する。"""

    @mcp.tool()
    async def list_templates() -> dict[str, Any]:
        """利用可能なテンプレート一覧を取得する。

        テンプレートストアに登録されているアプリケーションテンプレートの
        一覧（名称、説明、カスタマイズポイント）を返します。
        """
        try:
            templates = await app_service.list_templates()
            return {"templates": [t.model_dump() for t in templates]}
        except GalleyError as e:
            return {"error": type(e).__name__, "message": str(e)}

    @mcp.tool()
    async def scaffold_from_template(
        session_id: str,
        template_name: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """テンプレートからプロジェクトを生成する。

        指定されたテンプレートとパラメータからアプリケーションプロジェクトを
        スキャフォールディングします。

        Args:
            session_id: セッションID。
            template_name: テンプレート名。
            params: テンプレートパラメータ（任意）。
        """
        try:
            result = await app_service.scaffold_from_template(session_id, template_name, params or {})
            return dict(result)
        except (GalleyError, ValueError) as e:
            return {"error": type(e).__name__, "message": str(e)}

    @mcp.tool()
    async def update_app_code(
        session_id: str,
        file_path: str,
        new_content: str,
    ) -> dict[str, Any]:
        """アプリケーションコードを更新する。

        テンプレートから生成したアプリケーションのコードをカスタマイズします。
        更新前にスナップショットが自動保存されます。
        テンプレートのコア部分（protected_paths）は変更できません。

        Args:
            session_id: セッションID。
            file_path: 更新対象のファイルパス（app/からの相対パス）。
            new_content: 新しいファイル内容。
        """
        try:
            result = await app_service.update_app_code(session_id, file_path, new_content)
            return dict(result)
        except (GalleyError, ValueError) as e:
            return {"error": type(e).__name__, "message": str(e)}

    @mcp.tool()
    async def build_and_deploy(
        session_id: str,
        cluster_id: str,
        image_uri: str | None = None,
        namespace: str = "default",
    ) -> dict[str, Any]:
        """ビルド・デプロイを一括実行する。

        スキャフォールドされたアプリケーションをOKEクラスタにデプロイします。
        K8sマニフェスト（Deployment + Service）を自動生成し、
        kubectl applyでデプロイを実行します。

        image_uriを省略した場合、Build Instanceでイメージをビルドし
        OCIRにプッシュしてからデプロイします。

        Args:
            session_id: セッションID。
            cluster_id: OKEクラスタのOCID。
            image_uri: コンテナイメージURI（省略時はBuild Instanceでビルド）。
            namespace: K8s名前空間（デフォルト: default）。
        """
        try:
            result = await app_service.build_and_deploy(session_id, cluster_id, image_uri, namespace)
            return result.model_dump()
        except (GalleyError, ValueError, RuntimeError) as e:
            return {"error": type(e).__name__, "message": str(e)}

    @mcp.tool()
    async def check_app_status(session_id: str) -> dict[str, Any]:
        """アプリケーションのデプロイ状態を確認する。

        デプロイ状態、エンドポイント、ヘルスチェック結果を返します。

        Args:
            session_id: セッションID。
        """
        try:
            result = await app_service.check_app_status(session_id)
            return result.model_dump()
        except GalleyError as e:
            return {"error": type(e).__name__, "message": str(e)}
