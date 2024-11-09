from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from functools import wraps, partial
from typing import Callable

from ._callable_handler import CallableHandler, AsyncCallableHandler
from ._requester import ResponseFinalizer, Preparer
from ._types import IRouter, Hooks
from ..tools import HTTPMethod, MethodType


class Route(ABC):
    __slots__ = (
        '_path',
        '_method',
        '_func',
        '_method_type',
        '_is_async',
        '__self__',
        '_router',
        '_hooks',
        '_skip_preparer',
        '_skip_finalizer'
    )

    def __new__(
            cls,
            path: str,
            method: HTTPMethod,
            router: IRouter,
            *,
            func: Callable,
            hooks: Hooks,
            skip_preparer: bool = False,
            skip_finalizer: bool = False,
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
            hooks: Hooks,
            skip_preparer: bool = False,
            skip_finalizer: bool = False,
    ):
        self._path = path
        self._method = method
        self._func = func
        self._router = router

        self._hooks = hooks
        self._skip_preparer = skip_preparer
        self._skip_finalizer = skip_finalizer

        self._method_type: MethodType = MethodType.STATIC

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

    @property
    def hooks(self) -> Hooks:
        return self._hooks

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
            self._hooks.response_finalizer = self._get_wrapper(func)
            return func

        if func is None:
            return decorator
        else:
            return decorator(func)

    def prepare(self, func: Preparer | None = None) -> Callable:
        """
        Args:
            func (Preparer | None):
                Args preparer, used to prepare the args for request before it.
                The final value also must be `Args` instance.
                Executed after router's __prepare_args__

        Returns:
            Preparer: Wrapped function, used to prepare the args for request before it
        """
        def decorator(func: Preparer) -> Preparer:
            self._hooks.post_preparer = self._get_wrapper(func)
            return func

        if func is None:
            return decorator
        else:
            return decorator(func)


class _SyncRoute(Route):
    def __call__(self, *args, **kwargs):
        with CallableHandler(
            func=self._func,
            router=self._router,
            request_args=(args, kwargs),
            method_type=self._method_type,
            path=self.path,
            method=self._method,
            hooks=self._hooks,
            skip_preparer=self._skip_preparer,
            skip_finalizer=self._skip_finalizer,
        ) as response:
            return response


class _AsyncRoute(Route):
    async def __call__(self, *args, **kwargs):
        async with AsyncCallableHandler(
            func=self._func,
            router=self._router,
            request_args=(args, kwargs),
            method_type=self._method_type,
            path=self.path,
            method=self._method,
            hooks=self._hooks,
            skip_preparer=self._skip_preparer,
            skip_finalizer=self._skip_finalizer,
        ) as response:
            return response
