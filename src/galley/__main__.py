"""Galley MCPサーバーのコマンドラインエントリポイント。"""

if __name__ == "__main__":
    from galley.config import ServerConfig
    from galley.server import create_server

    config = ServerConfig()
    mcp = create_server(config)
    mcp.run(transport="streamable-http", host=config.host, port=config.port)
