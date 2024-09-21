from functools import wraps
from typing import Callable, Any
from sensei.client import Manager
from ._endpoint import CaseConverter
from ._requester import JsonFinalizer
from ._route import Route
from ..tools import HTTPMethod, set_method_type
from ..tools.utils import bind_attributes
from ._types import RoutedFunction, IRouter, SameModel


class Router(IRouter):
    __slots__ = "_manager", "_host", "_converters", "_json_finalizer"

    def __init__(
            self,
            host: str,
            manager: Manager | None = None,
            *,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            json_finalizer: JsonFinalizer | None = None
    ):
        self._manager = manager
        self._host = host

        self._converters = {
            'query_case': query_case,
            'body_case': body_case,
            'cookie_case': cookie_case,
            'header_case': header_case
        }
        self._json_finalizer = json_finalizer if json_finalizer else lambda x: x

    @property
    def manager(self) -> Manager | None:
        return self._manager

    def _finalize_json(self, json: dict[str, Any]) -> dict[str, Any]:
        return self._json_finalizer(json)

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
                default_host=self._host,
                case_converters=case_converters,
                json_finalizer=self._finalize_json
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

            bind_attributes(wrapper, route.finalize, route.prepare)  # type: ignore
            return wrapper

        return decorator

    def model(self, model_obj: SameModel | None = None) -> SameModel:
        def decorator(model_obj: SameModel) -> SameModel:
            model_obj.__router__ = self
            if hasattr(model_obj, '__finalize_json__'):
                self._json_finalizer = model_obj.__finalize_json__
            return model_obj

        if model_obj is None:
            return decorator  # type: ignore
        else:
            return decorator(model_obj)

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
