from __future__ import annotations

from functools import wraps
from typing import Callable
from sensei.client import Manager
from ._endpoint import CaseConverter
from ._requester import JsonFinalizer, Preparer
from ._route import Route
from ..tools import HTTPMethod, set_method_type, identical, MethodType
from sensei._utils import bind_attributes
from ._types import RoutedFunction, IRouter, SameModel
from ._hook import Hook
from sensei.types import IRateLimit
from sensei._descriptors import RateLimitAttr, PortAttr


class Router(IRouter):
    rate_limit = RateLimitAttr()
    port = PortAttr()

    def __init__(
            self,
            host: str,
            *,
            port: int | None = None,
            rate_limit: IRateLimit | None = None,
            manager: Manager | None = None,
            query_case: CaseConverter = identical,
            body_case: CaseConverter = identical,
            cookie_case: CaseConverter = identical,
            header_case: CaseConverter = identical,
            json_finalizer: JsonFinalizer = identical,
            args_preparer: Preparer = identical
    ):
        self._manager = manager
        self._host = host

        self.port = port
        self.rate_limit = rate_limit

        self._query_case = query_case
        self._body_case = body_case
        self._cookie_case = cookie_case
        self._header_case = header_case

        self._finalize_json = json_finalizer
        self._prepare_args = args_preparer
        self._linked_to_model: bool = False

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
                converters[key] = getattr(self, f'_{key}')

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
                host=self._host,
                port=self.port,
                rate_limit=self.rate_limit,
                case_converters=case_converters,
                json_finalizer=self._finalize_json,
                pre_preparer=self._prepare_args
            )

            def _setattrs(
                    instance,
                    func: Callable,
                    wrapper: Callable,
                    route: Route
            ) -> None:
                method_type = route.method_type = wrapper.__method_type__  # type: ignore
                if MethodType.self_method(method_type):
                    route.__self__ = instance
                    func.__self__ = instance

            if not route.is_async:
                @set_method_type
                @wraps(func)
                def wrapper(*args, **kwargs):
                    _setattrs(args[0], func, wrapper, route)
                    return route(*args, **kwargs)
            else:
                @set_method_type
                @wraps(func)
                async def wrapper(*args, **kwargs):
                    _setattrs(args[0], func, wrapper, route)
                    return await route(*args, **kwargs)

            bind_attributes(wrapper, route.finalize, route.prepare)  # type: ignore
            return wrapper

        return decorator

    def model(self, model_cls: SameModel | None = None) -> SameModel:
        def decorator(model_cls: SameModel) -> SameModel:
            if self._linked_to_model:
                raise ValueError('Only one model can be associated with a router')

            model_cls.__router__ = self
            self._linked_to_model = True

            hooks = Hook.values()

            for hook in hooks:
                if hook_fun := getattr(model_cls, hook, None):
                    setattr(self, hook[1:-2], hook_fun)

            return model_cls

        if model_cls is None:
            return decorator  # type: ignore
        else:
            return decorator(model_cls)

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
