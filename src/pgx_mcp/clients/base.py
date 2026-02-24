"""Base API client with rate limiting, retry, and caching."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from typing import Any

import httpx
from cachetools import TTLCache

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token-bucket rate limiter for async HTTP clients."""

    def __init__(self, rate: float) -> None:
        self._rate = rate
        self._min_interval = 1.0 / rate if rate > 0 else 0
        self._last_request_time = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until a request is allowed under the rate limit."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time
            if elapsed < self._min_interval:
                wait_time = self._min_interval - elapsed
                logger.debug("Rate limiter: waiting %.3fs", wait_time)
                await asyncio.sleep(wait_time)
            self._last_request_time = time.monotonic()


class BaseAPIClient:
    """Base class for all external API clients.

    Provides:
    - Shared httpx.AsyncClient with connection pooling
    - Token-bucket rate limiting
    - In-memory TTL cache for responses
    - Exponential backoff retry for transient failures
    """

    BASE_URL: str = ""
    DEFAULT_HEADERS: dict[str, str] = {}
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_BASE: float = 1.0
    TIMEOUT: float = 30.0

    def __init__(self, rate_limit: float, cache_ttl: int = 3600) -> None:
        self._rate_limiter = RateLimiter(rate_limit)
        self._cache: TTLCache[str, Any] = TTLCache(maxsize=512, ttl=cache_ttl)
        self._client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        """Initialize the HTTP client."""
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self.DEFAULT_HEADERS,
            timeout=self.TIMEOUT,
            follow_redirects=True,
        )

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("Client not started. Call start() first.")
        return self._client

    def _cache_key(self, method: str, url: str, **kwargs: Any) -> str:
        """Generate a deterministic cache key from request parameters."""
        raw = f"{method}:{url}:{sorted(kwargs.items())}"
        return hashlib.sha256(raw.encode()).hexdigest()

    async def _request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> Any:
        """Make an HTTP request with rate limiting, caching, and retry."""
        cache_key = self._cache_key(method, url, params=params, json=json)

        if use_cache and cache_key in self._cache:
            logger.debug("Cache hit: %s", url)
            return self._cache[cache_key]

        last_exception: Exception | None = None
        for attempt in range(self.MAX_RETRIES):
            await self._rate_limiter.acquire()
            try:
                response = await self.client.request(method, url, params=params, json=json)
                if response.status_code == 429:
                    retry_after = float(response.headers.get("Retry-After", str(2**attempt)))
                    logger.warning("Rate limited on %s, retrying in %.1fs", url, retry_after)
                    await asyncio.sleep(retry_after)
                    continue
                response.raise_for_status()
                data = response.json()
                if use_cache:
                    self._cache[cache_key] = data
                return data
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (500, 502, 503, 504):
                    last_exception = e
                    wait = self.RETRY_BACKOFF_BASE * (2**attempt)
                    logger.warning(
                        "Server error on %s (HTTP %d), retry %d in %.1fs",
                        url,
                        e.response.status_code,
                        attempt + 1,
                        wait,
                    )
                    await asyncio.sleep(wait)
                    continue
                raise
            except (httpx.ConnectError, httpx.ReadTimeout) as e:
                last_exception = e
                wait = self.RETRY_BACKOFF_BASE * (2**attempt)
                logger.warning("Connection error on %s, retry %d in %.1fs", url, attempt + 1, wait)
                await asyncio.sleep(wait)

        raise RuntimeError(f"Failed after {self.MAX_RETRIES} retries: {url}") from last_exception

    async def get(
        self, url: str, params: dict[str, Any] | None = None, **kwargs: Any
    ) -> Any:
        """HTTP GET with rate limiting, caching, and retry."""
        return await self._request("GET", url, params=params, **kwargs)

    async def post(
        self, url: str, json: dict[str, Any] | None = None, **kwargs: Any
    ) -> Any:
        """HTTP POST with rate limiting, caching, and retry."""
        return await self._request("POST", url, json=json, **kwargs)
