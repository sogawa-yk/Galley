"""FastMCPベースのMCPサーバーエントリポイント。"""

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from galley.config import ServerConfig
from galley.prompts.infra import register_infra_prompts
from galley.prompts.workflow import register_workflow_prompts
from galley.resources.design import register_design_resources
from galley.resources.hearing import register_hearing_resources
from galley.services.app import AppService
from galley.services.design import DesignService
from galley.services.hearing import HearingService
from galley.services.infra import InfraService
from galley.storage.service import StorageService
from galley.tools.app import register_app_tools
from galley.tools.design import register_design_tools
from galley.tools.export import register_export_tools
from galley.tools.hearing import register_hearing_tools
from galley.tools.infra import register_infra_tools


def create_server(config: ServerConfig | None = None) -> FastMCP:
    """Galley MCPサーバーを作成し、ツール・リソース・プロンプトを登録する。

    Args:
        config: サーバー設定。Noneの場合はデフォルト設定を使用。

    Returns:
        設定済みのFastMCPインスタンス。
    """
    if config is None:
        config = ServerConfig()

    mcp = FastMCP("galley")

    # データアクセス層
    storage = StorageService(data_dir=config.data_dir)

    # サービス層
    hearing_service = HearingService(storage=storage, config_dir=config.config_dir)
    design_service = DesignService(storage=storage, config_dir=config.config_dir)
    infra_service = InfraService(storage=storage, config_dir=config.config_dir)
    app_service = AppService(storage=storage, config_dir=config.config_dir, config=config)

    # MCPインターフェース登録 — ヒアリング層
    register_hearing_tools(mcp, hearing_service, config_dir=config.config_dir)
    register_hearing_resources(mcp, config.config_dir)

    # MCPインターフェース登録 — 設計層
    register_design_tools(mcp, design_service)
    register_export_tools(mcp, design_service)
    register_design_resources(mcp, config.config_dir)

    # MCPインターフェース登録 — インフラ層
    register_infra_tools(mcp, infra_service)

    # MCPインターフェース登録 — アプリケーション層
    register_app_tools(mcp, app_service)

    # MCPインターフェース登録 — プロンプト
    register_workflow_prompts(mcp)
    register_infra_prompts(mcp)

    # ヘルスチェックエンドポイント
    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request: Request) -> JSONResponse:
        return JSONResponse({"status": "ok"})

    return mcp
