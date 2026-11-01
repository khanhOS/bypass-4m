"""Kiểm tra URL và chặn truy cập mạng nội bộ (SSRF)."""
from __future__ import annotations
import asyncio
import ipaddress
import socket
from urllib.parse import urlsplit
from app.config import ALLOWED_INITIAL_HOSTS, MAX_URL_LENGTH

class URLSecurityError(ValueError):
    """URL không an toàn hoặc không thuộc phạm vi hỗ trợ."""

def validate_input_url(url: str) -> str:
    if not isinstance(url, str) or not url or len(url) > MAX_URL_LENGTH:
        raise URLSecurityError("URL trống hoặc vượt quá độ dài cho phép.")
    try:
        parsed = urlsplit(url.strip())
        port = parsed.port
    except ValueError as exc:
        raise URLSecurityError("Cấu trúc URL hoặc cổng không hợp lệ.") from exc
    if parsed.scheme not in {"http", "https"}:
        raise URLSecurityError("Chỉ chấp nhận URL HTTP hoặc HTTPS.")
    if not parsed.hostname or parsed.username or parsed.password:
        raise URLSecurityError("URL thiếu hostname hoặc chứa thông tin đăng nhập.")
    if port not in {None, 80, 443}:
        raise URLSecurityError("Cổng URL không được hỗ trợ.")
    host = parsed.hostname.lower().rstrip(".")
    if host not in ALLOWED_INITIAL_HOSTS:
        raise URLSecurityError("Hiện tại chỉ hỗ trợ link4m.net và www.link4m.net.")
    return url.strip()

async def is_public_http_url(url: str) -> bool:
    """Chỉ cho phép HTTP(S) tới hostname có toàn bộ IP phân giải là public."""
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            return False
        if parsed.username or parsed.password:
            return False
        host = parsed.hostname.rstrip(".").lower()
        if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
            return False
        try:
            ip = ipaddress.ip_address(host)
            return ip.is_global
        except ValueError:
            loop = asyncio.get_running_loop()
            records = await loop.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
            addresses = {record[4][0].split("%")[0] for record in records}
            return bool(addresses) and all(ipaddress.ip_address(addr).is_global for addr in addresses)
    except (ValueError, OSError, socket.gaierror):
        return False
