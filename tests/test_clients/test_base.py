"""Tests for base API client."""

from __future__ import annotations

import httpx
import pytest
import respx

from pgx_mcp.clients.base import BaseAPIClient, RateLimiter


class ConcreteClient(BaseAPIClient):
    """Concrete implementation for testing."""

    BASE_URL = "https://test.example.com"
    DEFAULT_HEADERS = {"User-Agent": "test"}


@pytest.fixture
async def client() -> ConcreteClient:
    c = ConcreteClient(rate_limit=100, cache_ttl=3600)
    await c.start()
    yield c
    await c.close()


class TestRateLimiter:
    async def test_allows_request(self) -> None:
        limiter = RateLimiter(rate=100)
        await limiter.acquire()

    async def test_client_not_started(self) -> None:
        c = ConcreteClient(rate_limit=100, cache_ttl=0)
        with pytest.raises(RuntimeError, match="not started"):
            _ = c.client


class TestBaseAPIClient:
    @respx.mock
    async def test_get_success(self, client: ConcreteClient) -> None:
        respx.get("https://test.example.com/test").mock(
            return_value=httpx.Response(200, json={"key": "value"})
        )
        result = await client.get("/test")
        assert result == {"key": "value"}

    @respx.mock
    async def test_caching(self) -> None:
        c = ConcreteClient(rate_limit=100, cache_ttl=3600)
        await c.start()
        try:
            route = respx.get("https://test.example.com/cached")
            route.mock(return_value=httpx.Response(200, json={"cached": True}))

            result1 = await c.get("/cached")
            result2 = await c.get("/cached")

            assert result1 == result2
            assert route.call_count == 1
        finally:
            await c.close()

    @respx.mock
    async def test_retry_on_server_error(self, client: ConcreteClient) -> None:
        route = respx.get("https://test.example.com/flaky")
        route.side_effect = [
            httpx.Response(500),
            httpx.Response(200, json={"ok": True}),
        ]
        client.RETRY_BACKOFF_BASE = 0.01
        result = await client.get("/flaky", use_cache=False)
        assert result == {"ok": True}
        assert route.call_count == 2

    @respx.mock
    async def test_retry_on_429(self, client: ConcreteClient) -> None:
        route = respx.get("https://test.example.com/limited")
        route.side_effect = [
            httpx.Response(429, headers={"Retry-After": "0.01"}),
            httpx.Response(200, json={"ok": True}),
        ]
        result = await client.get("/limited", use_cache=False)
        assert result == {"ok": True}

    @respx.mock
    async def test_raises_on_client_error(self, client: ConcreteClient) -> None:
        respx.get("https://test.example.com/notfound").mock(
            return_value=httpx.Response(404, json={"error": "not found"})
        )
        with pytest.raises(httpx.HTTPStatusError):
            await client.get("/notfound")
