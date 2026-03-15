"""Authentication module for {{app_name}}.

Protected file - do not modify.

This module provides JWT token verification. In production, configure
JWT_SECRET or JWT_JWKS_URL environment variables for real validation.
"""

import logging
import os

logger = logging.getLogger("{{app_name}}.auth")

# JWT configuration
# Set JWT_SECRET for symmetric (HS256) verification,
# or JWT_JWKS_URL for asymmetric (RS256) JWKS-based verification.
JWT_SECRET = os.environ.get("JWT_SECRET", "")
JWT_JWKS_URL = os.environ.get("JWT_JWKS_URL", "")

# Protected file - do not modify


async def verify_token(token: str) -> dict | None:
    """Verify authentication token and return claims.

    Args:
        token: Bearer token string (without 'Bearer ' prefix).

    Returns:
        Decoded token claims as dict, or None if verification fails.

    Note:
        This is a stub implementation. To enable real JWT verification:
        1. Install PyJWT: ``pip install PyJWT[crypto]``
        2. Set JWT_SECRET env var for HS256, or JWT_JWKS_URL for RS256
        3. Uncomment the verification code below
    """
    if not token:
        return None

    # --- STUB: Replace with real JWT verification ---
    # When no secret is configured, accept any non-empty token (dev mode)
    if not JWT_SECRET and not JWT_JWKS_URL:
        logger.warning("JWT verification disabled (no JWT_SECRET or JWT_JWKS_URL configured)")
        return {"sub": "dev-user", "mode": "stub"}

    # --- Real JWT verification (uncomment after installing PyJWT) ---
    # import jwt
    # try:
    #     claims = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    #     return claims
    # except jwt.InvalidTokenError as e:
    #     logger.warning("Token verification failed: %s", e)
    #     return None

    return None
