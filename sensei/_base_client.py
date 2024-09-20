from abc import abstractmethod, ABCMeta, ABC
from typing import Mapping, Any
from .types import IRateLimit, IResponse


class _ClientPropsMeta(ABCMeta):
    def __new__(
            cls,
            cls_name: str,
            bases: tuple[type[Any], ...],
            namespace: dict[str, Any],
    ):
        namespace['_rate_limit'] = None
        namespace['_port'] = None
        namespace['_default_headers'] = None
        return super().__new__(cls, cls_name, bases, namespace)

    @property
    def rate_limit(cls) -> IRateLimit:
        return cls._rate_limit

    @rate_limit.setter
    def rate_limit(cls, value: tuple[int, int] | IRateLimit) -> None:
        if isinstance(value, IRateLimit):
            cls._rate_limit = value
        else:
            raise TypeError('Value must implement IRateLimit interface')

    @property
    def port(cls) -> int:
        return cls._port

    @port.setter
    def port(cls, value: int) -> None:
        if isinstance(value, int) and 1 <= value <= 65535:
            cls._port = value
        else:
            raise ValueError('Port must be between 1 and 65535')

    @property
    def default_headers(cls) -> Mapping[str, str]:
        return cls._default_headers

    @default_headers.setter
    def default_headers(cls, value: Mapping[str, str]) -> None:
        if isinstance(value, Mapping):
            cls._default_headers = value
        else:
            raise TypeError('Value must be a mapping of headers to values')


class BaseClient(ABC, metaclass=_ClientPropsMeta):
    def __init__(
            self,
            host: str,
            port: int | None = None,
            context: IRateLimit | None = None,
            headers: Mapping[str, str] | None = None
    ):
        port = port or self.get_port()

        self._context = context or self.get_rate_limit()

        self._client_headers = headers or self.get_default_headers()

        if host.endswith('/'):
            host = host[:-1]

        self._host = host
        self._api_url = f'{host}:{port}' if port is not None else host

    @property
    def host(self) -> str:
        return self._host

    @property
    def context(self) -> IRateLimit:
        return self._context

    @classmethod
    def get_rate_limit(cls) -> IRateLimit | None:
        return cls._rate_limit

    @classmethod
    def set_rate_limit(cls, calls: int, period: int) -> None:
        cls.rate_limit = calls, period

    @classmethod
    def get_port(cls) -> int | None:
        return cls._port

    @classmethod
    def set_port(cls, port: int) -> None:
        cls.port = port

    @classmethod
    def get_default_headers(cls) -> Mapping[str, str] | None:
        return cls._default_headers

    @classmethod
    def set_default_headers(cls, headers: Mapping[str, str]) -> None:
        cls.default_headers = headers

    @abstractmethod
    def request(self, method: str, *args, **kwargs) -> IResponse:
        pass
