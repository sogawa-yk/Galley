"""FastMCPベースのMCPサーバーエントリポイント。"""

from fastmcp import FastMCP

from galley.config import ServerConfig
from galley.prompts.design import register_design_prompts
from galley.prompts.hearing import register_hearing_prompts
from galley.resources.design import register_design_resources
from galley.resources.hearing import register_hearing_resources
from galley.services.design import DesignService
from galley.services.hearing import HearingService
from galley.storage.service import StorageService
from galley.tools.design import register_design_tools
from galley.tools.export import register_export_tools
from galley.tools.hearing import register_hearing_tools


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

    # MCPインターフェース登録 — ヒアリング層
    register_hearing_tools(mcp, hearing_service)
    register_hearing_resources(mcp, config.config_dir)
    register_hearing_prompts(mcp)

    # MCPインターフェース登録 — 設計層
    register_design_tools(mcp, design_service)
    register_export_tools(mcp, design_service)
    register_design_resources(mcp, config.config_dir)
    register_design_prompts(mcp)

    return mcp
