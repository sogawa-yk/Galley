"""エクスポート系のMCPツール定義。"""

from typing import Any

from fastmcp import FastMCP

from galley.models.errors import GalleyError
from galley.services.design import DesignService


def register_export_tools(mcp: FastMCP, design_service: DesignService) -> None:
    """エクスポート関連のMCPツールを登録する。"""

    @mcp.tool()
    async def export_summary(session_id: str) -> dict[str, Any]:
        """要件サマリーをMarkdown形式で出力する。

        アーキテクチャのコンポーネント一覧、接続関係、ヒアリング結果を
        Markdown形式のサマリーとして出力します。

        Args:
            session_id: セッションID。
        """
        try:
            markdown = await design_service.export_summary(session_id)
            return {"markdown": markdown}
        except GalleyError as e:
            return {"error": type(e).__name__, "message": str(e)}

    @mcp.tool()
    async def export_mermaid(session_id: str) -> dict[str, Any]:
        """構成図をMermaid形式で出力する。

        アーキテクチャの構成図をMermaid記法で出力します。
        コンポーネントとその接続関係を視覚的に表現します。

        Args:
            session_id: セッションID。
        """
        try:
            mermaid_text = await design_service.export_mermaid(session_id)
            return {"mermaid": mermaid_text}
        except GalleyError as e:
            return {"error": type(e).__name__, "message": str(e)}

    @mcp.tool()
    async def export_iac(session_id: str) -> dict[str, Any]:
        """IaCテンプレート（Terraform）を出力する。

        アーキテクチャに基づいた動作するTerraformリソース定義を生成します。
        main.tf、variables.tf、components.tf が含まれます。
        生成されたファイルはサーバー側に自動的に書き出されます。
        返却される terraform_dir を run_terraform_plan にそのまま渡せます。

        Args:
            session_id: セッションID。
        """
        try:
            result = await design_service.export_iac(session_id)
            return result
        except GalleyError as e:
            return {"error": type(e).__name__, "message": str(e)}

    @mcp.tool()
    async def export_all(session_id: str) -> dict[str, Any]:
        """全成果物を一括出力する。

        Markdownサマリー、Mermaid構成図、Terraformテンプレートを一括で出力します。

        Args:
            session_id: セッションID。
        """
        try:
            result = await design_service.export_all(session_id)
            return result
        except GalleyError as e:
            return {"error": type(e).__name__, "message": str(e)}
