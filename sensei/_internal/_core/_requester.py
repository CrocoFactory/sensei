from abc import ABC, abstractmethod
from functools import wraps
from typing import Callable, Generic, Any
from ._endpoint import Endpoint, Args, ResponseModel
from sensei._base_client import BaseClient
from sensei.client import Client, AsyncClient
from sensei.types import IResponse, IRequest
from ..tools import identical

Preparer = Callable[[Args], Args]
ResponseFinalizer = Callable[[IResponse], ResponseModel]
JsonFinalizer = Callable[[dict[str, Any]], dict[str, Any]]


class _DecoratedResponse(IResponse):
    __slots__ = (
        "_response",
        "_json_finalizer"
    )

    def __init__(
            self,
            response: IResponse,
            json_finalizer: JsonFinalizer = identical
    ):
        self._response = response
        self._json_finalizer = json_finalizer

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
        "_post_preparer",
        "_response_finalizer",
        "_endpoint",
        "_json_finalizer",
        "_preparer"
    )

    def __new__(
            cls,
            client: BaseClient,
            endpoint: Endpoint,
            *,
            response_finalizer: ResponseFinalizer | None = None,
            json_finalizer: JsonFinalizer = identical,
            preparer: Preparer = identical,
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
            *,
            response_finalizer: ResponseFinalizer | None = None,
            json_finalizer: JsonFinalizer = identical,
            preparer: Preparer = identical,
    ):
        self._client = client
        self._response_finalizer = response_finalizer or self._finalize
        self._endpoint = endpoint
        self._json_finalizer = json_finalizer
        self._preparer = preparer

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
            *,
            response_finalizer: ResponseFinalizer | None = None,
            json_finalizer: JsonFinalizer = identical,
            preparer: Preparer = identical,
    ):
        super().__init__(
            client,
            endpoint,
            response_finalizer=response_finalizer,
            json_finalizer=json_finalizer,
            preparer=preparer
        )

    async def request(self, **kwargs) -> ResponseModel:
        client = self._client
        args = self._get_args(**kwargs)

        response = await client.request(**args)
        response = _DecoratedResponse(response, json_finalizer=self._json_finalizer)
        return self._response_finalizer(response)

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
            *,
            response_finalizer: ResponseFinalizer | None = None,
            json_finalizer: JsonFinalizer = identical,
            preparer: Preparer = identical,
    ):
        super().__init__(
            client,
            endpoint,
            response_finalizer=response_finalizer,
            json_finalizer=json_finalizer,
            preparer=preparer
        )

    def request(self, **kwargs) -> ResponseModel:
        client = self._client
        args = self._get_args(**kwargs)

        response = client.request(**args)
        response = _DecoratedResponse(response, json_finalizer=self._json_finalizer)
        return self._response_finalizer(response)
