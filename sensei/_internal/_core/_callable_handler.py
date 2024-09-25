from __future__ import annotations

import inspect
from typing import Callable, TypeVar, Generic, Any, get_origin, get_args
from typing_extensions import Self
from sensei.client import Manager, AsyncClient, Client
from sensei._base_client import BaseClient
from ._endpoint import Endpoint, ResponseModel, RESPONSE_TYPES, CaseConverter, Args
from ._requester import Requester, ResponseFinalizer, Preparer, JsonFinalizer
from ..tools import HTTPMethod, args_to_kwargs, MethodType, identical
from sensei.types import IRateLimit, IResponse
from ..tools.utils import is_coroutine_function

_Client = TypeVar('_Client', bound=BaseClient)
_RequestArgs = tuple[tuple[Any, ...], dict[str, Any]]


class _CallableHandler(Generic[_Client]):
    __slots__ = (
        '_func',
        '_manager',
        '_method',
        '_path',
        '_rate_limit',
        '_host',
        '_port',
        '_request_args',
        '_method_type',
        '_temp_client',
        '_response_finalizer',
        '_preparer',
        '_converters',
        '_json_finalizer',
    )

    def __init__(
            self,
            *,
            path: str,
            method: HTTPMethod,
            func: Callable,
            host: str,
            port: int | None = None,
            rate_limit: IRateLimit | None = None,
            request_args: _RequestArgs,
            method_type: MethodType,
            manager: Manager[_Client] | None,
            case_converters: dict[str, CaseConverter],
            response_finalizer: ResponseFinalizer | None = None,
            json_finalizer: JsonFinalizer = identical,
            pre_preparer: Preparer = identical,
            post_preparer: Preparer = identical,
    ):
        self._func = func
        self._manager = manager
        self._method = method
        self._path = path
        self._host = host
        self._port = port
        self._rate_limit = rate_limit

        self._request_args = request_args
        self._method_type = method_type
        self._temp_client: _Client | None = None
        self._converters = case_converters

        if is_coroutine_function(post_preparer):
            async def preparer(value: Args) -> Args:
                return await post_preparer(pre_preparer(value))
        else:
            def preparer(value: Args) -> Args:
                return post_preparer(pre_preparer(value))

        if response_finalizer:
            if is_coroutine_function(response_finalizer):
                async def finalizer(value: IResponse) -> ResponseModel:
                    return await response_finalizer(value)
            else:
                def finalizer(value: IResponse) -> ResponseModel:
                    return response_finalizer(value)
        else:
            finalizer = response_finalizer

        self._preparer = preparer
        self._response_finalizer = finalizer

        self._json_finalizer = json_finalizer

    def __make_endpoint(self) -> Endpoint:
        params = {}
        func = self._func
        method_type = self._method_type
        sig = inspect.signature(func)

        args = sig.parameters.values()

        skipped = False

        for param in args:
            if MethodType.self_method(method_type) and not skipped:
                skipped = True
                continue

            if param.default and param.default is not inspect.Parameter.empty:
                params[param.name] = param.annotation, param.default
            else:
                params[param.name] = param.annotation

        return_type = sig.return_annotation if sig.return_annotation is not inspect.Signature.empty else None

        if not Endpoint.is_response_type(return_type):
            if return_type is Self:
                if MethodType.self_method(method_type):
                    return_type = func.__self__  # type: ignore
                else:
                    raise ValueError('Response "Self" is only for instance and class methods')
            elif get_origin(return_type) is list and get_args(return_type)[0] is Self:
                if method_type is MethodType.CLASS:
                    return_type = list[func.__self__]  # type: ignore
                else:
                    raise ValueError(f'Response "list[Self]" is only for class methods')
            elif self._response_finalizer is None:
                raise ValueError(f'Response finalizer must be set, if response is not from: {RESPONSE_TYPES}')
            else:
                return_type = dict

        endpoint = Endpoint(self._path, self._method, params=params, response=return_type, **self._converters)
        return endpoint

    def _make_requester(self, client: BaseClient) -> Requester:
        endpoint = self.__make_endpoint()
        requester = Requester(
            client,
            endpoint,
            response_finalizer=self._response_finalizer,
            json_finalizer=self._json_finalizer,
            preparer=self._preparer
        )
        return requester

    def _get_request_args(self, client: BaseClient) -> tuple[Requester, dict]:
        if client.host != self._host:
            raise ValueError('Client host must be equal to default host')

        if client.port != self._port:
            raise ValueError('Client port must be equal to default port')

        requester = self._make_requester(client)
        kwargs = args_to_kwargs(self._func, *self._request_args[0], **self._request_args[1])
        method_type = self._method_type

        if MethodType.self_method(method_type):
            kwargs.popitem(False)

        return requester, kwargs


class AsyncCallableHandler(_CallableHandler[AsyncClient], Generic[ResponseModel]):
    async def __aenter__(self) -> ResponseModel:
        manager = self._manager
        if manager is None or manager.empty():
            client = AsyncClient(host=self._host, port=self._port, rate_limit=self._rate_limit)
            await client.__aenter__()
            self._temp_client = client
        else:
            client = manager.get()
            if not isinstance(client, AsyncClient):
                raise TypeError(f'Manager`s client must be type of {AsyncClient}')

        requester, kwargs = self._get_request_args(client)

        return await requester.request(**kwargs)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if client := self._temp_client:
            await client.__aexit__(exc_type, exc_val, exc_tb)
            self._temp_client = None


class CallableHandler(_CallableHandler[Client], Generic[ResponseModel]):
    def __enter__(self) -> ResponseModel:
        manager = self._manager
        if manager is None or manager.empty():
            client = Client(host=self._host, port=self._port, rate_limit=self._rate_limit)
            client.__enter__()
            self._temp_client = client
        else:
            client = manager.get()
            if not isinstance(client, Client):
                raise TypeError(f'Manager`s client must be type of {Client}')

        requester, kwargs = self._get_request_args(client)

        return requester.request(**kwargs)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if client := self._temp_client:
            client.__exit__(exc_type, exc_val, exc_tb)
            self._temp_client = None
