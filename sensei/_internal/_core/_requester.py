from abc import ABC, abstractmethod
from functools import wraps
from typing import Callable, Any, Generic
from ._endpoint import Endpoint, Args, ResponseModel
from sensei._base_client import BaseClient
from sensei.client import Client, AsyncClient
from sensei.types import IResponse

Initializer = Callable[..., Args]
Finalizer = Callable[[IResponse], ResponseModel]


class Requester(ABC, Generic[ResponseModel]):
    def __new__(
            cls,
            client: BaseClient,
            endpoint: Endpoint,
            initializer: Initializer | None = None,
            finalizer: Finalizer | None = None
    ):
        if isinstance(client, AsyncClient):
            return super().__new__(_AsyncRequester)
        elif isinstance(client, Client):
            return super().__new__(_Requester)
        else:
            raise ValueError("Client must be an instance of AsyncClient or Client")

    def __init__(
            self,
            client: BaseClient,
            endpoint: Endpoint,
            initializer: Initializer | None = None,
            finalizer: Finalizer | None = None
    ):
        self._client = client
        self._initializer = initializer or self._initialize
        self._finalizer = finalizer or self._finalize
        self._endpoint = endpoint

    @property
    def client(self) -> BaseClient:
        return self._client

    @property
    def endpoint(self) -> Endpoint:
        return self._endpoint

    def _initialize(self, **kwargs) -> dict[str, Any]:
        endpoint = self._endpoint
        return endpoint.get_args(**kwargs).model_dump(mode="json", exclude_none=True, by_alias=True)

    def _finalize(self, response: IResponse) -> ResponseModel:
        endpoint = self._endpoint
        return endpoint.get_response(response_obj=response)

    @abstractmethod
    def request(self, **kwargs) -> ResponseModel:
        pass


class _AsyncRequester(Requester):
    def __init__(
            self,
            client: BaseClient,
            endpoint: Endpoint,
            initializer: Initializer | None = None,
            finalizer: Finalizer | None = None
    ):
        super().__init__(client, endpoint, initializer, finalizer)

    async def request(self, **kwargs) -> ResponseModel:
        client = self._client
        endpoint = self._endpoint

        args = self._initializer(**kwargs)
        response = await client.request(endpoint.method, **args)
        return self._finalizer(response)

    async def decorate(self, func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            await self.request(**kwargs)

        return wrapper


class _Requester(Requester):
    def __init__(
            self,
            client: BaseClient,
            endpoint: Endpoint,
            initializer: Initializer | None = None,
            finalizer: Finalizer | None = None
    ):
        super().__init__(client, endpoint, initializer, finalizer)

    def request(self, **kwargs) -> ResponseModel:
        client = self._client
        endpoint = self._endpoint

        args = self._initializer(**kwargs)
        response = client.request(endpoint.method, **args)
        return self._finalizer(response)
