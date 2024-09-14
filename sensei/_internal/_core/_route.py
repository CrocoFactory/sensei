import inspect
from abc import ABC, abstractmethod
from typing import Callable, TypeVar
from sensei.client import Manager
from ..tools import HTTPMethod, MethodType
from sensei._base_client import BaseClient
from ._callable_handler import CallableHandler
from ._requester import Finalizer

_Client = TypeVar('_Client', bound=BaseClient)


class Route(ABC):
    def __new__(
            cls,
            path: str,
            method: HTTPMethod,
            /, *,
            func: Callable,
            manager: Manager[_Client],
            default_host: str
    ):
        if inspect.iscoroutinefunction(func):
            instance = super().__new__(_AsyncRoute)
            is_async = True
        else:
            instance = super().__new__(_SyncRoute)
            is_async = False

        instance.__init__(path, method, func=func, manager=manager, default_host=default_host)
        instance._is_async = is_async
        return instance

    def __init__(
            self,
            path: str,
            method: HTTPMethod,
            /, *,
            func: Callable,
            manager: Manager[_Client],
            default_host: str
    ):
        self._path = path
        self._method = method
        self._func = func
        self._manager = manager
        self._default_host = default_host

        self._wraps(func)

        self._finalizer: Finalizer | None = None
        self._method_type: MethodType = MethodType.STATIC
        self._is_async = None

    def _wraps(self, func: Callable) -> None:
        # Copy attributes from the function to emulate the function interface
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__
        self.__annotations__ = func.__annotations__  # type: ignore
        self.__defaults__ = func.__defaults__   # type: ignore
        self.__kwdefaults__ = func.__kwdefaults__   # type: ignore
        self.__code__ = func.__code__   # type: ignore
        self.__globals__ = func.__globals__     # type: ignore
        self.__dict__ = func.__dict__    # type: ignore
        self.__module__ = func.__module__  # type: ignore

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

    def finalizer(self, func: Finalizer | None = None) -> Callable:
        def decorator(func: Finalizer) -> Finalizer:
            self._finalizer = func
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
            finalizer=self._finalizer
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
            finalizer=self._finalizer
        ) as response:
            return response
