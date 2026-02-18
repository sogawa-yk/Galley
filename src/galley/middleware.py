"""URLトークン認証ミドルウェア。"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class TokenAuthMiddleware(BaseHTTPMiddleware):
    """クエリパラメータのtokenを検証するミドルウェア。

    GALLEY_URL_TOKEN が設定されている場合、/mcp へのリクエストに
    token クエリパラメータの一致を要求する。
    /health はヘルスチェック用のため検証をスキップする。
    """

    SKIP_PATHS = {"/health"}

    def __init__(self, app, url_token: str = ""):
        super().__init__(app)
        self.url_token = url_token

    async def dispatch(self, request: Request, call_next) -> Response:
        if not self.url_token:
            return await call_next(request)

        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        token = request.query_params.get("token", "")
        if token != self.url_token:
            return JSONResponse(
                {"error": "Unauthorized", "message": "Invalid or missing token"},
                status_code=401,
            )

        return await call_next(request)
