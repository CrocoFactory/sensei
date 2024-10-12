from __future__ import annotations

import inspect
from typing import Callable, TypeVar, Generic, Any, get_origin, get_args

from typing_extensions import Self

from sensei._base_client import BaseClient
from sensei._utils import get_base_url, normalize_url
from sensei.client import AsyncClient, Client
from sensei.types import IResponse
from ._endpoint import Endpoint, ResponseModel, RESPONSE_TYPES, CaseConverter, Args
from ._requester import Requester, ResponseFinalizer, Preparer, JsonFinalizer
from ._types import IRouter
from ..tools import HTTPMethod, args_to_kwargs, MethodType, identical
from ..tools.utils import is_coroutine_function

_Client = TypeVar('_Client', bound=BaseClient)
_RequestArgs = tuple[tuple[Any, ...], dict[str, Any]]


class _CallableHandler(Generic[_Client]):
    __slots__ = (
        '_func',
        '_method',
        '_path',
        '_host',
        '_request_args',
        '_method_type',
        '_temp_client',
        '_response_finalizer',
        '_preparer',
        '_converters',
        '_json_finalizer',
        '_router'
    )

    def __init__(
            self,
            *,
            path: str,
            method: HTTPMethod,
            router: IRouter,
            func: Callable,
            host: str,
            request_args: _RequestArgs,
            method_type: MethodType,
            case_converters: dict[str, CaseConverter],
            response_finalizer: ResponseFinalizer | None = None,
            json_finalizer: JsonFinalizer = identical,
            pre_preparer: Preparer = identical,
            post_preparer: Preparer = identical,
    ):
        self._func = func
        self._router = router
        self._method = method
        self._path = path
        self._host = host

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
                    raise ValueError('Response "list[Self]" is only for class methods')
            elif self._response_finalizer is None:
                raise ValueError(f'Response finalizer must be set, if response is not from: {RESPONSE_TYPES}')
            else:
                return_type = dict

        converters = self._converters.copy()
        converters.pop('response_case')
        endpoint = Endpoint(self._path, self._method, params=params, response=return_type, **converters)
        return endpoint

    def _make_requester(self, client: BaseClient) -> Requester:
        case_converter = self._converters.get('response_case', identical)
        endpoint = self.__make_endpoint()
        requester = Requester(
            client,
            endpoint,
            response_finalizer=self._response_finalizer,
            json_finalizer=self._json_finalizer,
            preparer=self._preparer,
            response_case=case_converter,
        )
        return requester

    def _get_request_args(self, client: BaseClient) -> tuple[Requester, dict]:
        if normalize_url(str(client.base_url)) != normalize_url(get_base_url(self._host, self._router.port)):
            raise ValueError('Client base url must be equal to Router base url')

        requester = self._make_requester(client)
        kwargs = args_to_kwargs(self._func, *self._request_args[0], **self._request_args[1])
        method_type = self._method_type

        if MethodType.self_method(method_type):
            kwargs.popitem(False)

        return requester, kwargs


class AsyncCallableHandler(_CallableHandler[AsyncClient], Generic[ResponseModel]):
    async def __aenter__(self) -> ResponseModel:
        router = self._router
        manager = router.manager
        if manager is None or manager.empty():
            client = AsyncClient(host=self._host, port=router.port, rate_limit=router.rate_limit)
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
        router = self._router
        manager = router.manager

        if manager is None or manager.empty():
            client = Client(host=self._host, port=router.port, rate_limit=router.rate_limit)
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
