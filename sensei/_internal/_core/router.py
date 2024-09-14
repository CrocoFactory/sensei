from functools import wraps
from typing import Callable, Protocol
from cytoolz.functoolz import MethodType
from sensei.client import Manager
from ._requester import Finalizer
from ._route import Route
from ..tools import HTTPMethod, set_method_type


class RoutedFunction(Protocol):
    def __call__(self, *args, **kwargs):
        ...

    finalizer: Callable[[Finalizer], Finalizer]
    __method_type__: MethodType
    __route__: Route


class Router:
    def __init__(self, default_host: str, manager: Manager | None = None):
        self._manager = manager
        self._default_host = default_host

    @property
    def manager(self) -> Manager | None:
        return self._manager

    def _get_decorator(self, path: str, /, *, method: HTTPMethod) -> Callable:
        def decorator(func: Callable) -> Callable:
            route = Route(path, method, func=func, manager=self._manager, default_host=self._default_host)

            if not route.is_async:
                @set_method_type
                @wraps(func)
                def wrapper(*args, **kwargs):
                    route.method_type = wrapper.__method_type__
                    return route(*args, **kwargs)
            else:
                @set_method_type
                @wraps(func)
                async def wrapper(*args, **kwargs):
                    route.method_type = wrapper.__method_type__
                    return await route(*args, **kwargs)

            setattr(wrapper, 'finalizer', route.finalizer)
            setattr(wrapper, '__route__', route)
            return wrapper

        return decorator

    def get(self, path: str, /) -> RoutedFunction:
        decorator = self._get_decorator(path, method="GET")
        return decorator

    def post(self, path: str, /) -> RoutedFunction:
        decorator = self._get_decorator(path, method="POST")
        return decorator

    def patch(self, path: str, /) -> RoutedFunction:
        decorator = self._get_decorator(path, method="PATCH")
        return decorator

    def put(self, path: str, /) -> RoutedFunction:
        decorator = self._get_decorator(path, method="PUT")
        return decorator

    def delete(self, path: str, /) -> RoutedFunction:
        decorator = self._get_decorator(path, method="DELETE")
        return decorator
