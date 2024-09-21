import inspect
from abc import ABC, abstractmethod
from typing import Callable, TypeVar
from sensei.client import Manager
from ._endpoint import CaseConverter
from ..tools import HTTPMethod, MethodType, identical
from sensei._base_client import BaseClient
from ._callable_handler import CallableHandler
from ._requester import ResponseFinalizer, Preparer, JsonFinalizer

_Client = TypeVar('_Client', bound=BaseClient)


class Route(ABC):
    __slots__ = (
        '_path',
        '_method',
        '_func',
        '_manager',
        '_default_host',
        '_response_finalizer',
        '_method_type',
        '_is_async',
        '_case_converters',
        '_preparer',
        '_json_finalizer',
        '_pre_preparer'
    )

    def __new__(
            cls,
            path: str,
            method: HTTPMethod,
            /, *,
            func: Callable,
            manager: Manager[_Client],
            default_host: str,
            case_converters: dict[str, CaseConverter],
            json_finalizer: JsonFinalizer = identical,
            pre_preparer: Preparer = identical,
    ):
        if inspect.iscoroutinefunction(func):
            instance = super().__new__(_AsyncRoute)
            is_async = True
        else:
            instance = super().__new__(_SyncRoute)
            is_async = False

        instance.__init__(
            path,
            method,
            func=func,
            manager=manager,
            default_host=default_host,
            case_converters=case_converters,
            json_finalizer=json_finalizer,
            pre_preparer=pre_preparer
        )
        instance._is_async = is_async

        return instance

    def __init__(
            self,
            path: str,
            method: HTTPMethod,
            /, *,
            func: Callable,
            manager: Manager[_Client],
            default_host: str,
            case_converters: dict[str, CaseConverter],
            json_finalizer: JsonFinalizer | None = None,
            pre_preparer: Preparer = identical,
    ):
        self._path = path
        self._method = method
        self._func = func
        self._manager = manager
        self._default_host = default_host

        self._response_finalizer: ResponseFinalizer | None = None
        self._preparer: Preparer = identical
        self._method_type: MethodType = MethodType.STATIC
        self._is_async = None

        self._case_converters = case_converters
        self._json_finalizer = json_finalizer
        self._pre_preparer = pre_preparer

    @property
    def path(self) -> str:
        return self._path

    @property
    def method(self) -> HTTPMethod:
        return self._method

    @property
    def is_async(self) -> bool:
        return self._is_async

    @abstractmethod
    def __call__(self, *args, **kwargs):
        pass

    @property
    def method_type(self) -> MethodType:
        return self._method_type

    @method_type.setter
    def method_type(self, value: MethodType):
        if isinstance(value, MethodType):
            self._method_type = value
        else:
            raise TypeError(f'Method type must be an instance of {MethodType.__class__}')

    def finalize(self, func: ResponseFinalizer | None = None) -> Callable:
        def decorator(func: ResponseFinalizer) -> ResponseFinalizer:
            self._response_finalizer = func
            return func

        if func is None:
            return decorator
        else:
            return decorator(func)

    def prepare(self, func: Preparer | None = None) -> Callable:
        def decorator(func: Preparer) -> Preparer:
            self._preparer = func
            return func

        if func is None:
            return decorator
        else:
            return decorator(func)


class _SyncRoute(Route):
    def __call__(self, *args, **kwargs):
        with CallableHandler(
            func=self._func,
            default_host=self._default_host,
            request_args=(args, kwargs),
            manager=self._manager,
            method_type=self._method_type,
            path=self.path,
            method=self._method,
            post_preparer=self._preparer,
            response_finalizer=self._response_finalizer,
            case_converters=self._case_converters,
            json_finalizer=self._json_finalizer,
            pre_preparer=self._pre_preparer
        ) as response:
            return response


class _AsyncRoute(Route):
    async def __call__(self, *args, **kwargs):
        async with CallableHandler(
            func=self._func,
            default_host=self._default_host,
            request_args=(args, kwargs),
            manager=self._manager,
            method_type=self._method_type,
            path=self.path,
            method=self._method,
            post_preparer=self._preparer,
            response_finalizer=self._response_finalizer,
            case_converters=self._case_converters,
            json_finalizer=self._json_finalizer,
            pre_preparer=self._pre_preparer
        ) as response:
            return response
