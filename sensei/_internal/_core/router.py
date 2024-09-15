from functools import wraps
from typing import Callable, Protocol
from sensei.client import Manager
from ._endpoint import CaseConverter
from ._requester import Finalizer
from ._route import Route
from ..tools import HTTPMethod, set_method_type, MethodType


class RoutedFunction(Protocol):
    def __call__(self, *args, **kwargs):
        ...

    def finalizer(self, finalizer: Finalizer) -> Finalizer:
        ...

    __method_type__: MethodType
    __route__: Route


class Router:
    def __init__(
            self,
            default_host: str,
            manager: Manager | None = None,
            *,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None
    ):
        self._manager = manager
        self._default_host = default_host

        self._converters = {
            'query_case': query_case,
            'body_case': body_case,
            'cookie_case': cookie_case,
            'header_case': header_case
        }

    @property
    def manager(self) -> Manager | None:
        return self._manager

    def _replace_default_converters(
            self,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None
    ) -> dict[str, CaseConverter]:
        converters = {
            'query_case': query_case,
            'body_case': body_case,
            'cookie_case': cookie_case,
            'header_case': header_case
        }

        for key, converter in converters.items():
            if converter is None:
                converters[key] = self._converters[key]

        return converters

    def _get_decorator(
            self,
            path: str,
            method: HTTPMethod,
            /, *,
            case_converters: dict[str, CaseConverter]
    ) -> Callable:
        def decorator(func: Callable) -> Callable:
            route = Route(
                path,
                method,
                func=func,
                manager=self._manager,
                default_host=self._default_host,
                case_converters=case_converters
            )

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

    def get(
            self,
            path: str,
            /, *,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None
    ) -> RoutedFunction:
        converters = self._replace_default_converters(query_case, body_case, cookie_case, header_case)

        decorator = self._get_decorator(
            path,
            "GET",
            case_converters=converters
        )
        return decorator

    def post(
            self,
            path: str,
            /, *,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None
    ) -> RoutedFunction:
        converters = self._replace_default_converters(query_case, body_case, cookie_case, header_case)

        decorator = self._get_decorator(
            path,
            "POST",
            case_converters=converters
        )
        return decorator

    def patch(
            self,
            path: str,
            /, *,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None
    ) -> RoutedFunction:
        converters = self._replace_default_converters(query_case, body_case, cookie_case, header_case)

        decorator = self._get_decorator(
            path,
            "PATCH",
            case_converters=converters
        )
        return decorator

    def put(
            self,
            path: str,
            /, *,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None
    ) -> RoutedFunction:
        converters = self._replace_default_converters(query_case, body_case, cookie_case, header_case)

        decorator = self._get_decorator(
            path,
            "PUT",
            case_converters=converters
        )
        return decorator

    def delete(
            self,
            path: str,
            /, *,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None
    ) -> RoutedFunction:
        converters = self._replace_default_converters(query_case, body_case, cookie_case, header_case)

        decorator = self._get_decorator(
            path,
            "DELETE",
            case_converters=converters
        )
        return decorator
