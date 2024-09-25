from __future__ import annotations

from abc import abstractmethod, ABC
from ._utils import get_base_url
from .types import IRateLimit, IResponse
from sensei._descriptors import RateLimitAttr, PortAttr


class _PortAttr(PortAttr):
    def __set__(self, obj: object, value: int) -> None:
        if not obj.__dict__.get('_port_set'):
            super().__set__(obj, value)
            obj.__dict__['_port_set'] = True
        else:
            raise AttributeError('Port can only be set at creation')


class BaseClient(ABC):
    rate_limit = RateLimitAttr()
    port = _PortAttr()

    def __init__(
            self,
            host: str,
            port: int | None = None,
            rate_limit: IRateLimit | None = None,
    ):
        self.rate_limit = rate_limit
        self.port = port

        if host.endswith('/'):
            host = host[:-1]

        self._host = host

        base_url = get_base_url(host, port)
        self._api_url = base_url

    @property
    def host(self) -> str:
        return self._host

    @abstractmethod
    def request(self, method: str, url: str, *args, **kwargs) -> IResponse:
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        pass
