from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request
from app.core.security import decode_token


def get_real_ip(request: Request) -> str:
    """Extract real client IP considering forward/proxy headers."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip.strip()
    return get_remote_address(request)


def get_user_or_ip(request: Request) -> str:
    """Extract authenticated user ID or fallback to client IP."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        payload = decode_token(token)
        if payload and "sub" in payload:
            return f"user:{payload['sub']}"
    return get_real_ip(request)


# Central Slowapi Limiter with in-memory storage (and Redis backend compatibility)
limiter = Limiter(key_func=get_real_ip, default_limits=[])
