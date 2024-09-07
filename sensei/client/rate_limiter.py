import asyncio
from abc import ABC, abstractmethod
import threading
from time import time, sleep
from sensei.types import IRateLimit


class RateLimit(IRateLimit):
    def __init__(self, calls: int, period: int) -> None:
        """
        Initialize the shared state for rate limiting.

        :param calls: Maximum number of requests allowed per period.
        :param period: Time period (in seconds) for the rate limit.
        """
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
        Attempt to acquire a token.

        :return: True if a token was acquired, False otherwise.
        """
        async with self._async_lock:
            return self._acquire()

    async def async_wait_for_slot(self) -> None:
        """
        Wait until a slot becomes available by periodically acquiring a token.
        """
        while not await self.async_acquire():
            # Wait for the rate limit period before trying again
            await asyncio.sleep(self.period / self.calls)

    def acquire(self) -> bool:
        """
        Synchronously attempt to acquire a token.

        :return: True if a token was acquired, False otherwise.
        """
        with self._thread_lock:
            return self._acquire()

    def wait_for_slot(self) -> None:
        """
        Wait until a slot becomes available by periodically acquiring a token.
        """
        while not self.acquire():
            # Wait for the rate limit period before trying again
            sleep(self.period / self.calls)


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
    def __init__(self, rate_limit: IRateLimit) -> None:
        """
        Initialize the asynchronous rate RateLimit with shared state.

        :param rate_limit: An instance of RateLimiterState to share between limiters.
        """
        super().__init__(rate_limit)

    async def acquire(self) -> bool:
        """
        Asynchronously attempt to acquire a token.

        :return: True if a token was acquired, False otherwise.
        """
        return await self._rate_limit.async_acquire()

    async def wait_for_slot(self) -> None:
        """
        Wait until a slot becomes available by periodically acquiring a token.
        """
        await self._rate_limit.async_wait_for_slot()


class RateLimiter(_BaseLimiter):
    def __init__(self, rate_limit: IRateLimit) -> None:
        """
        Initialize the synchronous rate limiter with shared state.

        :param rate_limit: An instance of RateLimit to share between limiters.
        """
        super().__init__(rate_limit)

    def acquire(self) -> bool:
        """
        Synchronously attempt to acquire a token.

        :return: True if a token was acquired, False otherwise.
        """
        return self._rate_limit.acquire()

    def wait_for_slot(self) -> None:
        """
        Wait until a slot becomes available by periodically acquiring a token.
        """
        self._rate_limit.wait_for_slot()
