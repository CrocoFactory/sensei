from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from typing import Callable, Generic, Any, Awaitable, Union
from ._endpoint import Endpoint, Args, ResponseModel, CaseConverter
from sensei._base_client import BaseClient
from sensei.client import Client, AsyncClient
from sensei.types import IResponse, IRequest, Json
from ..tools import identical
from sensei._utils import placeholders

Preparer = Callable[[Args], Union[Args, Awaitable[Args]]]
ResponseFinalizer = Callable[[IResponse], Union[ResponseModel, Awaitable[ResponseModel]]]
JsonFinalizer = Callable[[Json], Json]


class _DecoratedResponse(IResponse):
    __slots__ = (
        "_response",
        "_json_finalizer",
        "_response_case"
    )

    def __init__(
            self,
            response: IResponse,
            json_finalizer: JsonFinalizer = identical,
            response_case: CaseConverter = identical,
    ):
        self._response = response
        self._json_finalizer = json_finalizer
        self._response_case = response_case

    def json(self) -> Json:
        case = self._response_case
        json = self._response.json()
        json = {case(k): v for k, v in json.items()}
        return self._json_finalizer(json)

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
        "_preparer",
        "_is_async_preparer",
        "_is_async_response_finalizer",
        "_response_case"
    )

    def __new__(
            cls,
            client: BaseClient,
            endpoint: Endpoint,
            *,
            response_finalizer: ResponseFinalizer | None = None,
            json_finalizer: JsonFinalizer = identical,
            preparer: Preparer = identical,
            response_case: CaseConverter = identical,
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
            response_case: CaseConverter = identical,
    ):
        self._client = client
        self._response_finalizer = response_finalizer or self._finalize
        self._endpoint = endpoint
        self._json_finalizer = json_finalizer
        self._preparer = preparer
        self._is_async_preparer = inspect.iscoroutinefunction(self._preparer)
        self._is_async_response_finalizer = inspect.iscoroutinefunction(self._response_finalizer)
        self._response_case = response_case

    @property
    def client(self) -> BaseClient:
        return self._client

    @property
    def endpoint(self) -> Endpoint:
        return self._endpoint

    @staticmethod
    def _prepare(args: Args) -> Args:
        return args

    def _finalize(self, response: IResponse) -> ResponseModel:
        endpoint = self._endpoint
        return endpoint.get_response(response_obj=response)

    @abstractmethod
    def request(self, **kwargs) -> ResponseModel:
        pass

    def _dump_args(self, args: Args) -> dict[str, Any]:
        endpoint = self._endpoint
        args = args.model_dump(mode="json", exclude_none=True, by_alias=True)
        if placeholders(url := args['url']):
            raise ValueError(f'Path params of {url} params must be passed')
        return {'method': endpoint.method, **args}


class _AsyncRequester(Requester):
    async def _call_preparer(self, args: Args) -> Args:
        result = self._preparer(args)
        if self._is_async_preparer:
            result = await result
        return result

    async def _call_response_finalizer(self, response: IResponse) -> ResponseModel:
        result = self._response_finalizer(response)
        if self._is_async_response_finalizer:
            result = await result
        return result

    async def _get_args(self, **kwargs) -> dict[str, Any]:
        endpoint = self._endpoint
        args = endpoint.get_args(**kwargs)
        args = await self._call_preparer(args)
        return self._dump_args(args)

    async def request(self, **kwargs) -> ResponseModel:
        client = self._client
        args = await self._get_args(**kwargs)

        response = await client.request(**args)
        response.raise_for_status()
        response = _DecoratedResponse(response, json_finalizer=self._json_finalizer, response_case=self._response_case)
        return await self._call_response_finalizer(response)


class _Requester(Requester):
    def _call_preparer(self, args: Args) -> Args:
        result = self._preparer(args)
        if self._is_async_preparer:
            raise ValueError("If preparer is async, the route function must match it")
        return result

    def _call_response_finalizer(self, response: IResponse) -> ResponseModel:
        result = self._response_finalizer(response)
        if self._is_async_response_finalizer:
            raise ValueError("If response finalizer is async, the route function must match it")
        return result

    def _get_args(self, **kwargs) -> dict[str, Any]:
        endpoint = self._endpoint
        args = endpoint.get_args(**kwargs)
        args = self._call_preparer(args)
        return self._dump_args(args)

    def request(self, **kwargs) -> ResponseModel:
        client = self._client
        args = self._get_args(**kwargs)

        response = client.request(**args)
        response.raise_for_status()
        response = _DecoratedResponse(response, json_finalizer=self._json_finalizer, response_case=self._response_case)
        return self._call_response_finalizer(response)
