from typing import Callable
from sensei.client import Manager
from ._route import Route


class Router:
    def __init__(self, default_host: str, manager: Manager | None = None):
        self._manager = manager
        self._default_host = default_host

    @property
    def manager(self) -> Manager | None:
        return self._manager

    def get(self, path: str, /) -> Callable:
        def decorator(func: Callable) -> Route:
            return Route(path, 'GET', func=func, manager=self._manager, default_host=self._default_host)
        return decorator

    def post(self, path: str, /) -> Callable:
        def decorator(func: Callable) -> Route:
            return Route(path, 'POST', func=func, manager=self._manager, default_host=self._default_host)
        return decorator

    def patch(self, path: str, /) -> Callable:
        def decorator(func: Callable) -> Route:
            return Route(path, 'PATCH', func=func, manager=self._manager, default_host=self._default_host)
        return decorator

    def put(self, path: str, /) -> Callable:
        def decorator(func: Callable) -> Route:
            return Route(path, 'PUT', func=func, manager=self._manager, default_host=self._default_host)
        return decorator

    def delete(self, path: str, /) -> Callable:
        def decorator(func: Callable) -> Route:
            return Route(path, 'DELETE', func=func, manager=self._manager, default_host=self._default_host)
        return decorator
