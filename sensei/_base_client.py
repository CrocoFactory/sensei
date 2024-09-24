from __future__ import annotations

from abc import abstractmethod, ABC
from ._utils import get_path_params, fill_path_params
from .types import IRateLimit, IResponse
from sensei._descriptors import RateLimitAttr, PortAttr


class BaseClient(ABC):
    rate_limit = RateLimitAttr()
    port = PortAttr()

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

        if 'port' in get_path_params(host):
            api_url = fill_path_params(host, {'port': port})
        elif port is not None:
            api_url = f'{host}:{port}'
        else:
            api_url = host

        self._api_url = api_url

    @property
    def host(self) -> str:
        return self._host

    @abstractmethod
    def request(self, method: str, url: str, *args, **kwargs) -> IResponse:
        pass
