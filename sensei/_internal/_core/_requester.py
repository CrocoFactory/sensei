from abc import ABC, abstractmethod
from functools import wraps
from typing import Callable, Generic, Any
from ._endpoint import Endpoint, Args, ResponseModel
from sensei._base_client import BaseClient
from sensei.client import Client, AsyncClient
from sensei.types import IResponse, IRequest


Preparer = Callable[[Args], Args]
Finalizer = Callable[[IResponse], ResponseModel]
JsonFinalizer = Callable[[dict[str, Any]], dict[str, Any]]


class _DecoratedResponse(IResponse):
    def __init__(
            self,
            response: IResponse,
            json_finalizer: JsonFinalizer | None = None
    ):
        self._response = response
        self._json_finalizer = json_finalizer if json_finalizer is not None else lambda x: x

    def json(self) -> dict[str, Any]:
        return self._json_finalizer(self._response.json())

    def raise_for_status(self) -> IResponse:
        return self._response.raise_for_status()

    def request(self) -> IRequest:
        return self._response.request

    @property
    def text(self) -> str:
        return self._response.text

    @property
    def status_code(self) -> int:
        return self._response.status_code

    @property
    def content(self) -> bytes:
        return self._response.content


class Requester(ABC, Generic[ResponseModel]):
    __slots__ = (
        "_client",
        "_preparer",
        "_finalizer",
        "_endpoint"
    )

    def __new__(
            cls,
            client: BaseClient,
            endpoint: Endpoint,
            preparer: Preparer | None = None,
            finalizer: Finalizer | None = None,
            json_finalizer: JsonFinalizer | None = None
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
            preparer: Preparer | None = None,
            finalizer: Finalizer | None = None,
            json_finalizer: JsonFinalizer | None = None
    ):
        self._client = client
        self._preparer = preparer or self._prepare
        self._finalizer = finalizer or self._finalize
        self._endpoint = endpoint
        self._json_finalizer = json_finalizer

    @property
    def client(self) -> BaseClient:
        return self._client

    @property
    def endpoint(self) -> Endpoint:
        return self._endpoint

    @staticmethod
    def _prepare(args: Args) -> Args:
        return args

    def _get_args(self, **kwargs) -> dict[str, Any]:
        endpoint = self._endpoint
        args = endpoint.get_args(**kwargs)
        args = self._preparer(args).model_dump(mode="json", exclude_none=True, by_alias=True)

        return {'method': endpoint.method, **args}

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
            preparer: Preparer | None = None,
            finalizer: Finalizer | None = None,
            json_finalizer: JsonFinalizer | None = None
    ):
        super().__init__(client, endpoint, preparer, finalizer, json_finalizer)

    async def request(self, **kwargs) -> ResponseModel:
        client = self._client
        args = self._get_args(**kwargs)

        response = await client.request(**args)
        response = _DecoratedResponse(response, json_finalizer=self._json_finalizer)
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
            preparer: Preparer | None = None,
            finalizer: Finalizer | None = None,
            json_finalizer: JsonFinalizer | None = None
    ):
        super().__init__(client, endpoint, preparer, finalizer, json_finalizer)

    def request(self, **kwargs) -> ResponseModel:
        client = self._client
        args = self._get_args(**kwargs)

        response = client.request(**args)
        response = _DecoratedResponse(response, json_finalizer=self._json_finalizer)
        return self._finalizer(response)
