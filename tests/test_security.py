import pytest
from app.security import URLSecurityError, is_public_http_url, validate_input_url

def test_accepts_link4m_url():
    assert validate_input_url("https://link4m.net/abc").startswith("https://link4m.net/")

@pytest.mark.parametrize("url", [
    "javascript:alert(1)", "http://localhost/", "https://example.com/",
    "https://user:pass@link4m.net/x",
])
def test_rejects_invalid_or_unsupported_input(url):
    with pytest.raises(URLSecurityError):
        validate_input_url(url)

@pytest.mark.asyncio
async def test_blocks_private_ip():
    assert await is_public_http_url("http://127.0.0.1/") is False
    assert await is_public_http_url("http://169.254.169.254/") is False

@pytest.mark.asyncio
async def test_rejects_non_http_scheme():
    assert await is_public_http_url("file:///etc/passwd") is False
