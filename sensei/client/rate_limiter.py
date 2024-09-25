import asyncio
from abc import ABC, abstractmethod
import threading
from time import time, sleep
from sensei.types import IRateLimit


class RateLimit(IRateLimit):
    """
    A class that manages rate limiting by maintaining tokens and enforcing rate limits.

    Args:
        calls (int): The maximum number of requests allowed per period.
        period (int): The time period in seconds for the rate limit.
    """

    __slots__ = "_tokens", "_last_checked", "_async_lock", "_thread_lock"

    def __init__(self, calls: int, period: int) -> None:
        super().__init__(calls, period)
        self._tokens: int = calls  # Initial number of tokens equals rate_limit
        self._last_checked: float = time()  # Timestamp of the last check
        self._async_lock: asyncio.Lock = asyncio.Lock()  # Lock for synchronizing access
        self._thread_lock: threading.Lock = threading.Lock()

    def _acquire(self) -> bool:
        now: float = time()
        elapsed: float = now - self._last_checked

        # Replenish tokens based on elapsed time
        self._tokens += int(elapsed / self._period * self._calls)
        self._tokens = min(self._tokens, self._calls)  # Ensure tokens don't exceed rate_limit
        self._last_checked = now

        if self._tokens > 0:
            self._tokens -= 1  # Consume a token
            return True
        else:
            return False

    async def async_acquire(self) -> bool:
        """
        Asynchronously attempt to acquire a token.

        Returns:
            bool: True if a token was acquired, False otherwise.
        """
        async with self._async_lock:
            return self._acquire()

    async def async_wait_for_slot(self) -> None:
        """Asynchronously wait until a slot becomes available by periodically attempting to acquire a token."""
        while not await self.async_acquire():
            await asyncio.sleep(self._period / self._calls)

    def acquire(self) -> bool:
        """
        Synchronously attempt to acquire a token.

        Returns:
            bool: True if a token was acquired, False otherwise.
        """
        with self._thread_lock:
            return self._acquire()

    def wait_for_slot(self) -> None:
        """Synchronously wait until a slot becomes available by periodically attempting to acquire a token."""
        while not self.acquire():
            # Wait for the rate limit period before trying again
            sleep(self._period / self._calls)


class _BaseLimiter(ABC):
    def __init__(self, rate_limit: IRateLimit) -> None:
        self._rate_limit: IRateLimit = rate_limit

    @abstractmethod
    def acquire(self) -> bool:
        pass

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

    async def acquire(self) -> bool:
        """
        Asynchronously attempt to acquire a token.

        Returns:
            bool: True if a token was acquired, False otherwise.
        """
        return await self._rate_limit.async_acquire()

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

    def acquire(self) -> bool:
        """
        Synchronously attempt to acquire a token.

        Returns:
            bool: True if a token was acquired, False otherwise.
        """
        return self._rate_limit.acquire()

    def wait_for_slot(self) -> None:
        """Synchronously wait until a slot becomes available by periodically acquiring a token."""
        self._rate_limit.wait_for_slot()
