import asyncio
import threading
from abc import ABC, abstractmethod
from time import time, sleep

from sensei.types import IRateLimit


class RateLimit(IRateLimit):
    """
    The class that manages rate limiting by maintaining tokens and enforcing rate limits.
    This class implements a [token bucket](https://en.wikipedia.org/wiki/Token_bucket){.external-link}
    rate-limiting system.

    Example:
        ```python
        from sensei import RateLimit, Router

        calls, period = 1, 1
        rate_limit = RateLimit(calls, period)
        router = Router('https://example-api.com', rate_limit=rate_limit)

        @router.get('/users/{id_}')
        def get_user(id_: int) -> User:
            pass

        for i in range(5):
            get_user(i)  # Here code will be paused for 1 second after each iteration
        ```

    Args:
        calls (int): The maximum number of requests allowed per period.
        period (int): The time period in seconds for the rate limit.
    """

    __slots__ = "_tokens", "_last_checked", "_async_lock", "_thread_lock"

    def __init__(self, calls: int, period: int) -> None:
        super().__init__(calls, period)
        self._tokens: int = calls
        self._last_checked: float = time()
        self._async_lock: asyncio.Lock = asyncio.Lock()
        self._thread_lock: threading.Lock = threading.Lock()

    def __acquire(self) -> bool:
        now: float = time()
        elapsed: float = now - self._last_checked

        self._tokens += int(elapsed / self._period * self._calls)
        self._tokens = min(self._tokens, self._calls)
        self._last_checked = now

        if self._tokens > 0:
            self._tokens -= 1
            return True
        else:
            return False

    async def _async_acquire(self) -> bool:
        """
        Asynchronously attempt to acquire a token.

        Returns:
            bool: True if a token was acquired, False otherwise.
        """
        async with self._async_lock:
            return self.__acquire()

    async def async_wait_for_slot(self) -> None:
        """Asynchronously wait until a slot becomes available by periodically attempting to acquire a token."""
        while not await self._async_acquire():
            await asyncio.sleep(self._period / self._calls)

    def _acquire(self) -> bool:
        """
        Synchronously attempt to acquire a token.

        Returns:
            bool: True if a token was acquired, False otherwise.
        """
        with self._thread_lock:
            return self.__acquire()

    def wait_for_slot(self) -> None:
        """Synchronously wait until a slot becomes available by periodically attempting to acquire a token."""
        while not self._acquire():
            sleep(self._period / self._calls)


class _BaseLimiter(ABC):
    def __init__(self, rate_limit: IRateLimit) -> None:
        self._rate_limit: IRateLimit = rate_limit

    @abstractmethod
    def wait_for_slot(self) -> None:
        pass


class AsyncRateLimiter(_BaseLimiter):
    """
    Asynchronous rate limiter that manages request rate limiting using async methods.

    Args:
        rate_limit (IRateLimit): An instance of RateLimit to share between limiters.
    """

    def __init__(self, rate_limit: IRateLimit) -> None:
        super().__init__(rate_limit)

    async def wait_for_slot(self) -> None:
        """Asynchronously wait until a slot becomes available by periodically acquiring a token."""
        await self._rate_limit.async_wait_for_slot()


class RateLimiter(_BaseLimiter):
    """
    Synchronous rate limiter that manages request rate limiting using synchronous methods.

    Args:
        rate_limit (IRateLimit): An instance of RateLimit to share between limiters.
    """

    def __init__(self, rate_limit: IRateLimit) -> None:
        super().__init__(rate_limit)

    def wait_for_slot(self) -> None:
        """Synchronously wait until a slot becomes available by periodically acquiring a token."""
        self._rate_limit.wait_for_slot()
