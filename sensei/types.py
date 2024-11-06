from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, Mapping, Any, Union

from httpx import AsyncClient, Client
from typing_extensions import Self

Json = Union[dict, list[dict]]


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
    async def async_wait_for_slot(self) -> None:
        """
        Wait until a slot becomes available by periodically acquiring a token.
        """
        pass

    @abstractmethod
    def wait_for_slot(self) -> None:
        """
        Wait until a slot becomes available by periodically acquiring a token.
        """
        pass

    def _rate(self) -> float:
        return self._calls / self._period

    def __eq__(self, other: "IRateLimit") -> bool:
        return self._rate() == other._rate()

    def __lt__(self, other: "IRateLimit") -> bool:
        return self._rate() < other._rate()

    def __le__(self, other: "IRateLimit") -> bool:
        return self._rate() <= other._rate()

    def __gt__(self, other: "IRateLimit") -> bool:
        return self._rate() > other._rate()

    def __ge__(self, other: "IRateLimit") -> bool:
        return self._rate() >= other._rate()


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

    def json(self) -> Json:
        pass

    def raise_for_status(self) -> Self:
        pass

    @property
    def request(self) -> IRequest:
        pass

    @property
    def text(self) -> str:
        pass

    @property
    def status_code(self) -> int:
        pass

    @property
    def content(self) -> bytes:
        pass

    @property
    def headers(self) -> Mapping[str, Any]:
        pass


BaseClient = Union[AsyncClient, Client]
