"""MCPツール定義モジュール。"""

import functools
import logging
import time
from typing import Any, Callable

logger = logging.getLogger("galley.tools")


def log_tool_call(func: Callable[..., Any]) -> Callable[..., Any]:
    """MCPツール呼び出しのログを記録するデコレータ。"""

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        tool_name = func.__name__
        session_id = kwargs.get("session_id") or (args[0] if args else None)
        logger.info("Tool call: %s (session=%s)", tool_name, session_id)
        start = time.monotonic()
        try:
            result = await func(*args, **kwargs)
            elapsed = time.monotonic() - start
            logger.info("Tool done: %s (%.2fs)", tool_name, elapsed)
            return result
        except Exception:
            elapsed = time.monotonic() - start
            logger.exception("Tool error: %s (%.2fs)", tool_name, elapsed)
            raise

    return wrapper
