from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from typing import Generic, Any

from sensei._base_client import BaseClient
from sensei._utils import placeholders
from sensei.client import Client, AsyncClient
from sensei.types import IResponse, Json
from ._endpoint import Endpoint, Args, ResponseModel
from ._types import JsonFinalizer, ResponseFinalizer, Preparer, CaseConverters, CaseConverter
from ..tools import identical


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

    def __getattribute__(self, attr: str) -> Any:
        if attr not in ('json', '_response', '_json_finalizer', '_response_case'):
            return getattr(self._response, attr)
        else:
            return super().__getattribute__(attr)

    def json(self) -> Json:
        case = self._response_case
        json = self._response.json()
        json = {case(k): v for k, v in json.items()}
        return self._json_finalizer(json)


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
        "_case_converters"
    )

    def __new__(
            cls,
            client: BaseClient,
            endpoint: Endpoint,
            *,
            case_converters: CaseConverters,
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
            case_converters: CaseConverters,
            response_finalizer: ResponseFinalizer | None = None,
            json_finalizer: JsonFinalizer = identical,
            preparer: Preparer = identical,
    ):
        self._client = client
        self._response_finalizer = response_finalizer or self._finalize
        self._endpoint = endpoint
        self._json_finalizer = json_finalizer
        self._preparer = preparer
        self._is_async_preparer = inspect.iscoroutinefunction(self._preparer)
        self._is_async_response_finalizer = inspect.iscoroutinefunction(self._response_finalizer)
        self._case_converters = case_converters

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
        case = self._case_converters['response_case']
        response = _DecoratedResponse(response, json_finalizer=self._json_finalizer, response_case=case)
        response = await self._call_response_finalizer(response)
        self._endpoint.validate_response(response)
        return response


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
        case = self._case_converters['response_case']
        response = _DecoratedResponse(response, json_finalizer=self._json_finalizer, response_case=case)
        response = self._call_response_finalizer(response)
        self._endpoint.validate_response(response)
        return response
