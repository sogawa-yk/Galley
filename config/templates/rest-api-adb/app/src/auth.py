"""Authentication module - Protected file."""

# Protected file - do not modify


async def verify_token(token: str) -> bool:
    """Verify authentication token."""
    return len(token) > 0
