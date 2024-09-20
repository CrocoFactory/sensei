import inspect
from typing import Callable, TypeVar, Generic, Any, Self
from pydantic import BaseModel
from sensei.client import Manager, AsyncClient, Client
from sensei._base_client import BaseClient
from ._endpoint import Endpoint, ResponseModel, ResponseTypes, CaseConverter
from ._requester import Requester, Finalizer, Initializer
from ..tools import HTTPMethod, args_to_kwargs, MethodType

_Client = TypeVar('_Client', bound=BaseClient)
_RequestArgs = tuple[tuple[Any, ...], dict[str, Any]]


class _CallableHandler(Generic[_Client]):
    __slots__ = (
        '_func',
        '_manager',
        '_method',
        '_path',
        '_default_host',
        '_request_args',
        '_method_type',
        '_temp_client',
        '_finalizer',
        '_initializer',
        '_converters'
    )

    def __init__(
            self,
            *,
            path: str,
            method: HTTPMethod,
            func: Callable,
            default_host: str,
            request_args: _RequestArgs,
            method_type: MethodType,
            manager: Manager[_Client] | None,
            finalizer: Finalizer | None,
            initializer: Initializer | None,
            case_converters: dict[str, CaseConverter]
    ):
        self._func = func
        self._manager = manager
        self._method = method
        self._path = path
        self._default_host = default_host
        self._request_args = request_args
        self._method_type = method_type
        self._temp_client: _Client | None = None
        self._converters = case_converters

        self._initializer = initializer
        self._finalizer = finalizer

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

        if return_type is not None and return_type not in ResponseTypes and not isinstance(return_type,
                                                                                           type(BaseModel)):
            if return_type == Self:
                if MethodType.self_method(method_type):
                    return_type = func.__self__  # type: ignore
                else:
                    raise ValueError(f'Response is "Self" is only set for instance and class methods')
            elif self._finalizer is None:
                raise ValueError(f'Finalizer must be configured, if response is not from: {ResponseTypes}')
            else:
                return_type = dict

        endpoint = Endpoint(self._path, self._method, params=params, response=return_type, **self._converters)
        return endpoint

    def _make_requester(self, client: BaseClient) -> Requester:
        endpoint = self.__make_endpoint()
        requester = Requester(client, endpoint, initializer=self._initializer, finalizer=self._finalizer)
        return requester

    def _get_request_args(self, client: BaseClient) -> tuple[Requester, dict]:
        requester = self._make_requester(client)
        kwargs = args_to_kwargs(self._func, *self._request_args[0], **self._request_args[1])
        method_type = self._method_type

        if MethodType.self_method(method_type):
            kwargs.popitem(False)

        return requester, kwargs


class AsyncCallableHandler(_CallableHandler[AsyncClient], Generic[ResponseModel]):
    def __init__(
            self,
            *,
            method: HTTPMethod,
            path: str,
            func: Callable,
            default_host: str,
            request_args: _RequestArgs,
            method_type: MethodType,
            manager: Manager[AsyncClient] | None = None,
            finalizer: Finalizer | None = None,
            initializer: Initializer | None,
            case_converters: dict[str, CaseConverter]
    ):
        super().__init__(
            func=func,
            default_host=default_host,
            request_args=request_args,
            manager=manager,
            method=method,
            method_type=method_type,
            path=path,
            initializer=initializer,
            finalizer=finalizer,
            case_converters=case_converters
        )

    async def __aenter__(self) -> ResponseModel:
        manager = self._manager
        if manager is None or manager.empty():
            client = AsyncClient(host=self._default_host)
            await client.__aenter__()
            self._temp_client = client
        else:
            client = manager.get()

        requester, kwargs = self._get_request_args(client)

        return await requester.request(**kwargs)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if client := self._temp_client:
            await client.__aexit__(exc_type, exc_val, exc_tb)
            self._temp_client = None


class CallableHandler(_CallableHandler[Client], Generic[ResponseModel]):
    def __init__(
            self,
            *,
            method: HTTPMethod,
            path: str,
            func: Callable,
            default_host: str,
            request_args: _RequestArgs,
            method_type: MethodType,
            manager: Manager[Client] | None = None,
            finalizer: Finalizer | None = None,
            initializer: Initializer | None,
            case_converters: dict[str, CaseConverter]
    ):
        super().__init__(
            func=func,
            default_host=default_host,
            request_args=request_args,
            manager=manager,
            method_type=method_type,
            method=method,
            path=path,
            finalizer=finalizer,
            initializer=initializer,
            case_converters=case_converters
        )

    def __enter__(self) -> ResponseModel:
        manager = self._manager
        if manager is None or manager.empty():
            client = Client(host=self._default_host)
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
