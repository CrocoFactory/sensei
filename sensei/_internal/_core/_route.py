from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from functools import wraps, partial
from typing import Callable, TypeVar

from sensei._base_client import BaseClient
from ._callable_handler import CallableHandler, AsyncCallableHandler
from ._case_converters import CaseConverters
from ._requester import ResponseFinalizer, Preparer, JsonFinalizer
from ._types import IRouter
from ..tools import HTTPMethod, MethodType, identical

_Client = TypeVar('_Client', bound=BaseClient)


class Route(ABC):
    __slots__ = (
        '_path',
        '_method',
        '_func',
        '_host',
        '_response_finalizer',
        '_method_type',
        '_is_async',
        '_case_converters',
        '_preparer',
        '_json_finalizer',
        '_pre_preparer',
        '__self__',
        '_router',
    )

    def __new__(
            cls,
            path: str,
            method: HTTPMethod,
            router: IRouter,
            *,
            func: Callable,
            host: str,
            case_converters: CaseConverters,
            json_finalizer: JsonFinalizer = identical,
            pre_preparer: Preparer = identical,
    ):
        if inspect.iscoroutinefunction(func):
            instance = super().__new__(_AsyncRoute)
            is_async = True
        else:
            instance = super().__new__(_SyncRoute)
            is_async = False

        instance._is_async = is_async

        return instance

    def __init__(
            self,
            path: str,
            method: HTTPMethod,
            router: IRouter,
            *,
            func: Callable,
            host: str,
            case_converters: CaseConverters,
            json_finalizer: JsonFinalizer | None = None,
            pre_preparer: Preparer = identical,
    ):
        self._path = path
        self._method = method
        self._func = func
        self._router = router

        self._host = host
        self._response_finalizer: ResponseFinalizer | None = None
        self._preparer: Preparer = identical
        self._method_type: MethodType = MethodType.STATIC

        self._case_converters = case_converters
        self._json_finalizer = json_finalizer
        self._pre_preparer = pre_preparer
        self.__self__: object | None = None

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
            raise TypeError(f'Method type must be an instance of {MethodType}')

    def _get_wrapper(self, func: Callable[..., ...]):
        @wraps(func)
        def wrapper(*args, **kwargs):
            new_func = func

            if self.__self__ is not None:
                new_func = partial(func, self.__self__)

            return new_func(*args, **kwargs)

        return wrapper

    def finalize(self, func: ResponseFinalizer | None = None) -> Callable:
        """
        Args:
            func (ResponseFinalizer | None):
                Response finalizer, used to modify final response, primarily when the response type of routed
                function is not from category of automatically handled types. Executed after router's __finalize_json__

        Returns:
            ResponseFinalizer: Wrapped function, used to finalize response
        """
        def decorator(func: ResponseFinalizer) -> ResponseFinalizer:
            self._response_finalizer = self._get_wrapper(func)
            return func

        if func is None:
            return decorator
        else:
            return decorator(func)

    def prepare(self, func: Preparer | None = None) -> Callable:
        """
        Args:
            func (Preparer | None):
                Args preparer, used to prepare the args for request before it. The final value also must be `Args` instance.
                Executed after router's __prepare_args__

        Returns:
            Preparer: Wrapped function, used to prepare the args for request before it
        """
        def decorator(func: Preparer) -> Preparer:
            self._preparer = self._get_wrapper(func)
            return func

        if func is None:
            return decorator
        else:
            return decorator(func)


class _SyncRoute(Route):
    def __call__(self, *args, **kwargs):
        with CallableHandler(
            func=self._func,
            host=self._host,
            router=self._router,
            request_args=(args, kwargs),
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
        async with AsyncCallableHandler(
            func=self._func,
            host=self._host,
            router=self._router,
            request_args=(args, kwargs),
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
