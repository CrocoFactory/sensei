from abc import ABC, abstractmethod
from typing import Protocol, Mapping, Self, Any


class IRateLimit(ABC):
    __slots__ = "_calls", "_period"

    def __init__(self, calls: int, period: int) -> None:
        """
        Initialize the shared state for rate limiting.

        :param calls: Maximum number of requests allowed per period.
        :param period: Time period (in seconds) for the rate limit.
        """
        self._calls: int = calls
        self._period: int = period

    @property
    def period(self) -> int:
        return self._period

    @period.setter
    def period(self, period: int) -> None:
        self._period = period

    @property
    def calls(self):
        return self._calls

    @calls.setter
    def calls(self, rate_limit: int) -> None:
        self._calls = rate_limit

    @abstractmethod
    async def async_acquire(self) -> bool:
        """
        Attempt to acquire a token.

        :return: True if a token was acquired, False otherwise.
        """
        pass

    @abstractmethod
    async def async_wait_for_slot(self) -> None:
        """
        Wait until a slot becomes available by periodically acquiring a token.
        """
        pass

    @abstractmethod
    def acquire(self) -> bool:
        """
        Synchronously attempt to acquire a token.

        :return: True if a token was acquired, False otherwise.
        """
        pass

    @abstractmethod
    def wait_for_slot(self) -> None:
        """
        Wait until a slot becomes available by periodically acquiring a token.
        """
        pass


class IRequest(Protocol):
    @property
    def headers(self) -> Mapping[str, Any]:
        pass

    @property
    def method(self) -> str:
        pass

    @property
    def url(self) -> Any:
        pass


class IResponse(Protocol):
    __slots__ = ()

    def __await__(self):
        pass

    @abstractmethod
    def json(self) -> dict[str, Any] | list:
        pass

    @abstractmethod
    def raise_for_status(self) -> Self:
        pass

    @property
    @abstractmethod
    def request(self) -> IRequest:
        pass

    @property
    @abstractmethod
    def text(self) -> str:
        pass

    @property
    @abstractmethod
    def status_code(self) -> int:
        pass

    @property
    @abstractmethod
    def content(self) -> bytes:
        pass
