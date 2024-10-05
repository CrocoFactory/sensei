from __future__ import annotations
from functools import wraps
from httpx import URL
from typing import Callable, Optional, Any
from sensei.client import Manager
from ._endpoint import CaseConverter
from ._requester import JsonFinalizer, Preparer
from ._route import Route
from ..tools import HTTPMethod, set_method_type, identical, MethodType
from sensei._utils import bind_attributes, get_base_url
from ._types import RoutedFunction, IRouter, RoutedModel
from ._hook import Hook
from sensei.types import IRateLimit
from sensei._descriptors import RateLimitAttr, PortAttr
from sensei.cases import header_case as to_header_case

_RouteDecorator = Callable[[Callable], RoutedFunction]


class Router(IRouter):
    """
    Router for managing API routes and handling HTTP requests.

    The `Router` class provides decorators for defining API endpoints with various HTTP methods
    (GET, POST, PATCH, PUT, DELETE). It handles URL construction, request preparation, JSON finalization,
    and rate limiting.

    Args:
        host (str):
            The root URL of the associated API. It may contain a colon and a placeholder for the port, e.g., `:{port}`.
            If a port is provided, it will replace the placeholder.
        port (Optional[int], optional):
            The port number of the associated API. If `None`, the port placeholder in `host` will not be replaced.
            Defaults to `None`.
        rate_limit (Optional[IRateLimit], optional):
            An object implementing the `IRateLimit` interface to handle API rate limiting.
            Defaults to `None`.
        manager (Optional[Manager], optional):
            A `Manager` instance used to provide an HTTP client to the router.
            Defaults to `None`.
        query_case (CaseConverter, optional):
            A converter function for the case of query parameters.
            Defaults to `identical`.
        body_case (CaseConverter, optional):
            A converter function for the case of body parameters.
            Defaults to `identical`.
        cookie_case (CaseConverter, optional):
            A converter function for the case of cookies.
            Defaults to `identical`.
        header_case (CaseConverter, optional):
            A converter function for the case of headers.
            Defaults to `identical`.
        __finalize_json__ (JsonFinalizer, optional):
            A function to finalize the JSON response. The final value must be JSON serializable.
            Defaults to `identical`.
        __prepare_args__ (Preparer, optional):
            A preparer function used to prepare the arguments for the request before it is sent.
            The final value must be an instance of `Args`. Defaults to `identical`.
    """

    rate_limit = RateLimitAttr()
    port = PortAttr()

    def __init__(
            self,
            host: str,
            *,
            port: Optional[int] = None,
            rate_limit: Optional[IRateLimit] = None,
            manager: Optional[Manager] = None,
            query_case: CaseConverter = identical,
            body_case: CaseConverter = identical,
            cookie_case: CaseConverter = identical,
            header_case: CaseConverter = to_header_case,
            response_case: CaseConverter = identical,
            __finalize_json__: JsonFinalizer = identical,
            __prepare_args__: Preparer = identical
    ):
        self._manager = manager
        self._host = host

        self.port = port
        self.rate_limit = rate_limit

        self._query_case = query_case
        self._body_case = body_case
        self._cookie_case = cookie_case
        self._header_case = header_case
        self._response_case = response_case

        self._finalize_json = __finalize_json__
        self._prepare_args = __prepare_args__
        self._linked_to_model: bool = False

    @property
    def base_url(self) -> URL:
        """
        Get the base URL constructed from the host and port.

        Returns:
            str: The base URL.
        """
        host = self._host
        port = self.port
        base = get_base_url(host, port)
        return URL(base)

    @property
    def manager(self) -> Optional[Manager]:
        """
        Get the manager used to provide an HTTP client to the router.

        Returns:
            Optional[Manager]: The `Manager` instance if set; otherwise, `None`.
        """
        return self._manager

    def _replace_default_converters(
            self,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            response_case: CaseConverter | None = None,
    ) -> dict[str, CaseConverter]:
        """
        Replace default case converters with provided ones if any.

        Args:
            query_case (CaseConverter | None, optional):
                Case converter for query parameters. Defaults to `None`.
            body_case (CaseConverter | None, optional):
                Case converter for body parameters. Defaults to `None`.
            cookie_case (CaseConverter | None, optional):
                Case converter for cookies. Defaults to `None`.
            header_case (CaseConverter | None, optional):
                Case converter for headers. Defaults to `None`.

        Returns:
            dict[str, CaseConverter]: A dictionary mapping parameter types to their converters.
        """
        converters = {
            'query_case': query_case,
            'body_case': body_case,
            'cookie_case': cookie_case,
            'header_case': header_case,
            'response_case': response_case,
        }

        for key, converter in converters.items():
            if converter is None:
                converters[key] = getattr(self, f'_{key}')

        return converters

    def _get_decorator(
            self,
            path: str,
            method: HTTPMethod,
            *,
            case_converters: dict[str, CaseConverter],
            skip_finalizer: bool = False,
            skip_preparer: bool = False,
    ) -> Callable:
        """
        Create a decorator for a specific HTTP method and path.

        Args:
            path (str):
                The relative path of the route.
            method (HTTPMethod):
                The HTTP method for the route (e.g., GET, POST).
            case_converters (dict[str, CaseConverter]):
                A dictionary of case converters for query, body, cookie, and header parameters.
            skip_finalizer (bool):
                Skip JSON finalizer, when finalizing response. Defaults to `False`.
            skip_preparer (bool):
                Skip preparing the arguments for the request. Defaults to `False`.

        Returns:
            Callable: A decorator that transforms a function into a routed function.
        """

        def decorator(func: Callable) -> Callable:
            json_finalizer = identical if skip_finalizer else self._finalize_json
            pre_preparer = identical if skip_preparer else self._prepare_args
            route = Route(
                path=path,
                method=method,
                func=func,
                manager=self._manager,
                host=self._host,
                port=self.port,
                rate_limit=self.rate_limit,
                case_converters=case_converters,
                json_finalizer=json_finalizer,
                pre_preparer=pre_preparer
            )

            def _setattrs(
                    instance: Any,
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
                    instance = args[0] if len(args) else None
                    _setattrs(instance, func, wrapper, route)
                    res = route(*args, **kwargs)
                    _setattrs(None, func, wrapper, route)
                    return res
            else:
                @set_method_type
                @wraps(func)
                async def wrapper(*args, **kwargs):
                    instance = args[0] if len(args) else None
                    _setattrs(instance, func, wrapper, route)
                    res = await route(*args, **kwargs)
                    _setattrs(None, func, wrapper, route)
                    return res

            bind_attributes(wrapper, route.finalize, route.prepare)  # type: ignore
            return wrapper

        return decorator

    def model(self, model_cls: Optional[RoutedModel] = None) -> RoutedModel:
        """
        Associate a model class with the router to enable "routed" methods and `dunder` hooks.

        This method modifies a class derived from `APIModel` to work seamlessly with the router,
        allowing the use of routed methods and special hooks.

        Args:
            model_cls (Optional[RoutedModel], optional):
                The class to be modified. If `None`, returns a decorator for later use.
                Defaults to `None`.

        Raises:
            ValueError: If a model is already linked to the router.
        """

        def decorator(model_cls: RoutedModel) -> RoutedModel:
            if self._linked_to_model:
                raise ValueError('Only one model can be associated with a router')

            model_cls.__router__ = self
            self._linked_to_model = True

            hooks = Hook.values()

            for hook in hooks:
                hook_fun = getattr(model_cls, hook, None)
                if hook_fun:
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
            header_case: CaseConverter | None = None,
            response_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
            skip_preparer: bool = False,
    ) -> _RouteDecorator:
        """
        Create a route using the HTTP GET method.

        This decorator transforms a function into a routed function that sends a GET request
        to the specified path, handling parameter case conversion and argument validation.

        Args:
            path (str):
                The relative path of the route.
            query_case (CaseConverter | None, optional):
                Case converter for query parameters. Defaults to using the router's default.
            body_case (CaseConverter | None, optional):
                Case converter for body parameters. Defaults to using the router's default.
            cookie_case (CaseConverter | None, optional):
                Case converter for cookie parameters. Defaults to using the router's default.
            header_case (CaseConverter | None, optional):
                Case converter for header parameters. Defaults to using the router's default.
            response_case (CaseConverter | None, optional):
                Case converter for JSON response. Defaults to using the router's default.
            skip_finalizer (bool):
                Skip JSON finalizer, when finalizing response. Defaults to `False`.
            skip_preparer (bool):
                Skip preparing the arguments for the request. Defaults to `False`.

        Returns:
            RoutedFunction: A routed function that sends a GET request according to the specified path and validates
            its arguments based on type annotations.

        Raises:
            pydantic_core.ValidationError: If type validation of arguments fails.
        """
        converters = self._replace_default_converters(query_case, body_case, cookie_case, header_case, response_case)

        decorator = self._get_decorator(
            path=path,
            method="GET",
            case_converters=converters,
            skip_finalizer=skip_finalizer,
            skip_preparer=skip_preparer,
        )
        return decorator

    def post(
            self,
            path: str,
            /, *,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            response_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
            skip_preparer: bool = False,
    ) -> _RouteDecorator:
        """
        Create a route using the HTTP POST method.

        This decorator transforms a function into a routed function that sends a POST request
        to the specified path, handling parameter case conversion and argument validation.

        Args:
            path (str):
                The relative path of the route.
            query_case (CaseConverter | None, optional):
                Case converter for query parameters. Defaults to using the router's default.
            body_case (CaseConverter | None, optional):
                Case converter for body parameters. Defaults to using the router's default.
            cookie_case (CaseConverter | None, optional):
                Case converter for cookie parameters. Defaults to using the router's default.
            header_case (CaseConverter | None, optional):
                Case converter for header parameters. Defaults to using the router's default.
            response_case (CaseConverter | None, optional):
                Case converter for JSON response. Defaults to using the router's default.
            skip_finalizer (bool):
                Skip JSON finalizer, when finalizing response. Defaults to `False`.
            skip_preparer (bool):
                Skip preparing the arguments for the request. Defaults to `False`.

        Returns:
            RoutedFunction: A routed function that sends a POST request according to the specified path and validates
            its arguments based on type annotations.

        Raises:
            pydantic_core.ValidationError: If type validation of arguments fails.
        """
        converters = self._replace_default_converters(query_case, body_case, cookie_case, header_case, response_case)

        decorator = self._get_decorator(
            path=path,
            method="POST",
            case_converters=converters,
            skip_finalizer=skip_finalizer,
            skip_preparer=skip_preparer,
        )
        return decorator

    def patch(
            self,
            path: str,
            /, *,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            response_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
            skip_preparer: bool = False,
    ) -> _RouteDecorator:
        """
        Create a route using the HTTP PATCH method.

        This decorator transforms a function into a routed function that sends a PATCH request
        to the specified path, handling parameter case conversion and argument validation.

        Args:
            path (str):
                The relative path of the route.
            query_case (CaseConverter | None, optional):
                Case converter for query parameters. Defaults to using the router's default.
            body_case (CaseConverter | None, optional):
                Case converter for body parameters. Defaults to using the router's default.
            cookie_case (CaseConverter | None, optional):
                Case converter for cookie parameters. Defaults to using the router's default.
            header_case (CaseConverter | None, optional):
                Case converter for header parameters. Defaults to using the router's default.
            response_case (CaseConverter | None, optional):
                Case converter for JSON response. Defaults to using the router's default.
            skip_finalizer (bool):
                Skip JSON finalizer, when finalizing response. Defaults to `False`.
            skip_preparer (bool):
                Skip preparing the arguments for the request. Defaults to `False`.

        Returns:
            RoutedFunction: A routed function that sends a PATCH request according to the specified path and validates
            its arguments based on type annotations.

        Raises:
            pydantic_core.ValidationError: If type validation of arguments fails.
        """
        converters = self._replace_default_converters(query_case, body_case, cookie_case, header_case, response_case)

        decorator = self._get_decorator(
            path=path,
            method="PATCH",
            case_converters=converters,
            skip_finalizer=skip_finalizer,
            skip_preparer=skip_preparer,
        )
        return decorator

    def put(
            self,
            path: str,
            /, *,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            response_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
            skip_preparer: bool = False,
    ) -> _RouteDecorator:
        """
        Create a route using the HTTP PUT method.

        This decorator transforms a function into a routed function that sends a PUT request
        to the specified path, handling parameter case conversion and argument validation.

        Args:
            path (str):
                The relative path of the route.
            query_case (CaseConverter | None, optional):
                Case converter for query parameters. Defaults to using the router's default.
            body_case (CaseConverter | None, optional):
                Case converter for body parameters. Defaults to using the router's default.
            cookie_case (CaseConverter | None, optional):
                Case converter for cookie parameters. Defaults to using the router's default.
            header_case (CaseConverter | None, optional):
                Case converter for header parameters. Defaults to using the router's default.
            response_case:
                Case converter for JSON response. Defaults to using the router's default.
            skip_finalizer:
                Skip JSON finalizer, when finalizing response. Defaults to `False`.
            skip_preparer (bool):
                Skip preparing the arguments for the request. Defaults to `False`.

        Returns:
            RoutedFunction: A routed function that sends a PUT request according to the specified path and validates
            its arguments based on type annotations.

        Raises:
            pydantic_core.ValidationError: If type validation of arguments fails.
        """
        converters = self._replace_default_converters(query_case, body_case, cookie_case, header_case, response_case)

        decorator = self._get_decorator(
            path=path,
            method="PUT",
            case_converters=converters,
            skip_finalizer=skip_finalizer,
            skip_preparer=skip_preparer,
        )
        return decorator

    def delete(
            self,
            path: str,
            /, *,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            response_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
            skip_preparer: bool = False,
    ) -> _RouteDecorator:
        """
        Create a route using the HTTP DELETE method.

        This decorator transforms a function into a routed function that sends a DELETE request
        to the specified path, handling parameter case conversion and argument validation.

        Args:
            path (str):
                The relative path of the route.
            query_case (CaseConverter | None, optional):
                Case converter for query parameters. Defaults to using the router's default.
            body_case (CaseConverter | None, optional):
                Case converter for body parameters. Defaults to using the router's default.
            cookie_case (CaseConverter | None, optional):
                Case converter for cookie parameters. Defaults to using the router's default.
            header_case (CaseConverter | None, optional):
                Case converter for header parameters. Defaults to using the router's default.
            response_case:
                Case converter for JSON response. Defaults to using the router's default.
            skip_finalizer:
                Skip JSON finalizer, when finalizing response. Defaults to `False`.
            skip_preparer (bool):
                Skip preparing the arguments for the request. Defaults to `False`.

        Returns:
            RoutedFunction: A routed function that sends a DELETE request according to the specified path and validates
            its arguments based on type annotations.

        Raises:
            pydantic_core.ValidationError: If type validation of arguments fails.
        """
        converters = self._replace_default_converters(query_case, body_case, cookie_case, header_case, response_case)

        decorator = self._get_decorator(
            path=path,
            method="DELETE",
            case_converters=converters,
            skip_finalizer=skip_finalizer,
            skip_preparer=skip_preparer,
        )
        return decorator
