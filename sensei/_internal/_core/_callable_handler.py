from __future__ import annotations

import inspect
from inspect import isclass
from typing import Callable, TypeVar, Generic, Any, get_origin, get_args

from httpx import Client, AsyncClient
from typing_extensions import Self

from sensei._utils import normalize_url
from sensei.types import IResponse, BaseClient
from ._endpoint import Endpoint, ResponseModel, RESPONSE_TYPES
from ._requester import Requester
from ._types import IRouter, Hooks
from .args import Args
from ..tools import HTTPMethod, args_to_kwargs, MethodType
from ..tools.utils import is_coroutine_function, identical

_Client = TypeVar('_Client', bound=BaseClient)
_RequestArgs = tuple[tuple[Any, ...], dict[str, Any]]


class _CallableHandler(Generic[_Client]):
    __slots__ = (
        '_func',
        '_method',
        '_path',
        '_request_args',
        '_method_type',
        '_temp_client',
        '_response_finalizer',
        '_preparer',
        '_case_converters',
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
            request_args: _RequestArgs,
            method_type: MethodType,
            hooks: Hooks,
            skip_preparer: bool = False,
            skip_finalizer: bool = False,
    ):
        self._func = func
        self._router = router
        self._method = method
        self._path = path

        self._request_args = request_args
        self._method_type = method_type
        self._temp_client: _Client | None = None
        self._case_converters = hooks.case_converters

        if skip_preparer:
            hooks.prepare_args = identical

        if skip_finalizer:
            hooks.finalize_json = identical

        post_preparer = hooks.post_preparer
        pre_preparer = hooks.prepare_args

        json_finalizer = hooks.finalize_json
        response_finalizer = hooks.response_finalizer

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

        old_single_self = False
        old_list_self = False
        func_self = getattr(func, '__self__', None)
        is_list = get_origin(return_type) is list

        single_list = list_elem = False
        if is_list:
            single_list = len((args := get_args(return_type))) == 1
            list_elem = args[0]

        if func_self is not None:
            class_name = func_self.__name__ if isclass(func_self) else func_self.__class__.__name__

            if is_list and single_list and isinstance(list_elem, str):
                return_type = list_elem

            if isinstance(return_type, str):
                if not is_list:
                    old_single_self = class_name == return_type
                else:
                    old_list_self = class_name == return_type

        if not Endpoint.is_response_type(return_type):
            if return_type is Self or old_single_self:
                if MethodType.self_method(method_type):
                    return_type = func.__self__  # type: ignore
                else:
                    raise ValueError('Response "Self" is only for instance and class methods')
            elif (is_list and single_list and list_elem is Self) or old_list_self:
                if method_type is MethodType.CLASS:
                    return_type = list[func.__self__]  # type: ignore
                else:
                    raise ValueError('Response "list[Self]" is only for class methods')
            elif self._response_finalizer is None:
                raise ValueError(f'Response finalizer must be set, if response is not from: {RESPONSE_TYPES}')

        endpoint = Endpoint(
            self._path,
            self._method,
            params=params,
            response=return_type,
            case_converters=self._case_converters,
        )
        return endpoint

    def _make_requester(self, client: BaseClient) -> Requester:
        endpoint = self.__make_endpoint()
        requester = Requester(
            client,
            endpoint,
            rate_limit=self._router.rate_limit,
            response_finalizer=self._response_finalizer,
            json_finalizer=self._json_finalizer,
            preparer=self._preparer,
            case_converters=self._case_converters,
        )
        return requester

    def _get_request_args(self, client: BaseClient) -> tuple[Requester, dict]:
        if normalize_url(str(client.base_url)) != normalize_url(str(self._router.base_url)):
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

        client = None
        if manager is not None:
            client = manager.get(is_async=True)

        if manager is None or client is None:
            client = AsyncClient(base_url=self._router.base_url)
            await client.__aenter__()
            self._temp_client = client
        else:
            client = manager.get(True)

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

        client = None
        if manager is not None:
            client = manager.get()

        if manager is None or client is None:
            client = Client(base_url=self._router.base_url)
            client.__enter__()
            self._temp_client = client
        else:
            client = manager.get()

        requester, kwargs = self._get_request_args(client)

        return requester.request(**kwargs)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if client := self._temp_client:
            client.__exit__(exc_type, exc_val, exc_tb)
            self._temp_client = None
