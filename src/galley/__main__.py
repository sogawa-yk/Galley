"""Galley MCPサーバーのコマンドラインエントリポイント。"""

if __name__ == "__main__":
    import uvicorn
    from starlette.middleware import Middleware

    from galley.config import ServerConfig
    from galley.middleware import TokenAuthMiddleware
    from galley.server import create_server

    config = ServerConfig()
    mcp = create_server(config)
    app = mcp.http_app(
        transport="streamable-http",
        middleware=[Middleware(TokenAuthMiddleware, url_token=config.url_token)],
    )
    uvicorn.run(app, host=config.host, port=config.port)
