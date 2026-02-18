"""Galley MCPサーバーのコマンドラインエントリポイント。"""

if __name__ == "__main__":
    from galley.server import create_server

    mcp = create_server()
    mcp.run()
