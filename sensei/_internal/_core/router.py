from __future__ import annotations

from functools import wraps
from typing import Callable, Optional, Any, TypeVar

from httpx import URL

from sensei._utils import get_base_url
from sensei.cases import header_case as to_header_case
from sensei.client import Manager
from sensei.types import IRateLimit
from ._requester import JsonFinalizer
from ._route import Route
from ._types import IRouter, Preparer, RoutedFunction, CaseConverters, CaseConverter, Hooks
from ..tools import HTTPMethod, set_method_type, identical, MethodType, bind_attributes

_KT = TypeVar('_KT')
_VT = TypeVar('_VT')
_RF = TypeVar('_RF', bound=RoutedFunction)


_RouteDecorator = Callable[[_RF], _RF]


class Router(IRouter):
    def __init__(
            self,
            host: str,
            *,
            port: Optional[int] = None,
            rate_limit: Optional[IRateLimit] = None,
            manager: Optional[Manager] = None,
            default_case: CaseConverter | None = None,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = to_header_case,
            response_case: CaseConverter | None = None,
            __finalize_json__: JsonFinalizer = identical,
            __prepare_args__: Preparer = identical
    ):
        """
        Router for managing API routes and handling HTTP requests.
        Provides decorators for defining API endpoints with various HTTP methods:

        - GET
        - POST
        - PATCH
        - PUT
        - DELETE
        - HEAD
        - OPTIONS

        Import it directly from Sensei:

        ```python
        from sensei import Router
        ```

        Example:
            ```python
            from typing import Annotated
            from sensei import Router, Path, APIModel

            router = Router('https://pokeapi.co/api/v2/')


            class Pokemon(APIModel):
                name: str
                id: int
                height: int
                weight: int


            @router.get('/pokemon/{name}')
            def get_pokemon(name: Annotated[str, Path(max_length=300)]) -> Pokemon:
                pass

            pokemon = get_pokemon(name="pikachu")
            print(pokemon)
            ```

        Args:
            host:
                The root URL of the associated API. It may contain a colon and a placeholder for the port, e.g., `:{port}`.
                If a port is provided, it will replace the placeholder.

                **Example**

                ```python
                from sensei import Router

                router = Router(host="https://exqmple-api.com:{port}/api/v1", port=3000)
                ```
            port (int, optional):
                The port number of the associated API. If `None`, the port placeholder in `host` will not be replaced.
            rate_limit (IRateLimit, optional):
                An object implementing the `IRateLimit` interface to handle API rate limiting.

                **Example**
                ```python
                from sensei import RateLimit, Router

                calls, period = 1, 1
                rate_limit = RateLimit(calls, period)
                router = Router('https://example-api.com', rate_limit=rate_limit)

                @router.get('/users/{id_}')
                def get_user(id_: int) -> User:
                    pass

                for i in range(5):
                    get_user(i)  # Here code will be paused for 1 second after each iteration
                ```
            manager (Manager, optional):
                A `Manager` instance used to provide an HTTP client to the router.

                **Example**
                ```python
                from sensei import Manager, Router, Client

                manager = Manager()
                router = Router('httpx://example-api.com', manager=manager)

                @router.get('/users/{id_}')
                def get_user(id_: int) -> User:
                    pass

                with Client(base_url=router.base_url) as client:
                    manager.set(client)
                    user = get_user(1)
                    print(user)
                    manager.pop()
                ```
            default_case (CaseConverter, optional):
                Case converter for all parameters.
            query_case (CaseConverter, optional):
                Case converter of query parameters.

                **Example**
                ```python
                from sensei import Router, camel_case, snake_case

                router = Router(
                    'https://api.example.com',
                    query_case=camel_case,
                    response_case=snake_case
                )

                @router.get('/users')
                def get_user(id: int) -> User:
                    pass
                ```
            body_case (CaseConverter, optional):
                Case converter of body.
            cookie_case (CaseConverter, optional):
                Case converter of cookies.
            header_case (CaseConverter, optional):
                Case converter of headers.
            response_case (CaseConverter, optional):
                Case converter of JSON response.
            __finalize_json__ (JsonFinalizer, optional):
                A function to finalize the JSON response. It's applied for each routed function, associated with the Router
                The final value must be JSON serializable. Can be represented as **async function**.

                JSON finalizer is used for JSON response transformation before internal or user-defined response finalizing.

                **Example**
                ```python
                from sensei import Router
                from typing import Any

                def _finalize_json(json: dict[str, Any]) -> dict[str, Any]:
                    return json['data']

                router = Router('https://api.example.com', __finalize_json__=_finalize_json)
                ```

            __prepare_args__ (Preparer, optional):
                A preparer function used to prepare the arguments for the request before it is sent. It's applied for
                each routed function, associated with the Router. The final value must be an instance of `Args`.
                Can be represented as **async function**.

                Preparer is executed after internal argument parsing. So, all request parameters are available in
                `Args` model within a preparer.

                **Example**
                ```python
                from sensei import APIModel, Router, Args

                class Context:
                    token: str


                def prepare_args(args: Args) -> Args:
                    args.headers['Authorization'] = f'Bearer {Context.token}'
                    return args

                router = Router('https://api.example.com', __prepare_args__=prepare_args)
                ```
        """
        self._manager = manager
        self._host = host

        self._port = port
        self._rate_limit = rate_limit

        self._default_case = default_case
        self._query_case = query_case
        self._body_case = body_case
        self._cookie_case = cookie_case
        self._header_case = header_case
        self._response_case = response_case

        self._finalize_json = __finalize_json__
        self._prepare_args = __prepare_args__

    @property
    def base_url(self) -> URL:
        """
        Get the base URL constructed from the host and port.

        Returns:
            str: The base URL.
        """
        host = self._host
        port = self._port
        base = get_base_url(host, port)
        return URL(base)

    @property
    def port(self) -> int:
        """
        Get the port number of the associated API.

        Returns:
            int: The port number of the associated API. If `None`, the port placeholder in `host` will not be replaced.
        """
        return self._port

    @port.setter
    def port(self, value: int) -> None:
        """
        Set the port number of the associated API.

        Args:
            value (int):
                A port number
        """
        if value is None or isinstance(value, int) and 1 <= value <= 65535:
            self._port = value
        else:
            raise ValueError('Port must be between 1 and 65535')

    @property
    def rate_limit(self) -> IRateLimit:
        """
        Get the rate limit used to handle API rate limiting.

        Returns:
            IRateLimit: An object implementing the `IRateLimit` interface to handle API rate limiting. Defaults to `None`.
        """
        return self._rate_limit

    @rate_limit.setter
    def rate_limit(self, value: IRateLimit) -> None:
        """
        Set the RateLimit used to handle API rate limiting.

        Args:
            value (IRateLimit):
                An object implementing the `IRateLimit`
        """
        if value is None or isinstance(value, IRateLimit):
            self._rate_limit = value
        else:
            raise TypeError(f'Value must implement {IRateLimit} interface')

    @property
    def manager(self) -> Optional[Manager]:
        """
        Get the manager used to provide an HTTP client to the router.

        Returns:
            Manager: The `Manager` instance if set; otherwise, `None`.
        """
        return self._manager

    @manager.setter
    def manager(self, value: Manager) -> None:
        """
        Set the manager used to provide an HTTP client to the router.

        Args:
            value (Manager, optional):
                A `Manager` instance used to provide an HTTP client to the router.
                Defaults to `None`.
        """
        if not isinstance(value, Manager):
            raise TypeError(f'Manager must be an instance of {Manager}')
        else:
            self._manager = value

    @property
    def default_case(self) -> CaseConverter | None:
        """
        Returns:
             CaseConverter: Case converter for all parameters.
        """
        return self._default_case

    @property
    def query_case(self) -> CaseConverter | None:
        """
        Returns:
             CaseConverter: Case converter of query parameters.
        """
        return self._query_case

    @property
    def body_case(self) -> CaseConverter | None:
        """
        Returns:
             CaseConverter: Case converter of body parameters.
        """
        return self._body_case

    @property
    def cookie_case(self) -> CaseConverter | None:
        """
        Returns:
             CaseConverter: Case converter of cookies.
        """
        return self._cookie_case

    @property
    def header_case(self) -> CaseConverter | None:
        """
        Returns:
             CaseConverter: Case converter of headers.
        """
        return self._header_case

    @property
    def response_case(self) -> CaseConverter | None:
        """
        Returns:
             CaseConverter: Case converter of JSON response.
        """
        return self._response_case

    def _get_decorator(
            self,
            path: str,
            method: HTTPMethod,
            *,
            case_converters: CaseConverters,
            skip_finalizer: bool = False,
            skip_preparer: bool = False,
    ) -> Callable:
        def decorator(func: Callable) -> Callable:
            hooks = Hooks(
                case_converters=case_converters,
                finalize_json=self._finalize_json,
                prepare_args=self._prepare_args,
            )

            route = Route(
                path=path,
                method=method,
                router=self,
                func=func,
                hooks=hooks,
                skip_preparer=skip_preparer,
                skip_finalizer=skip_finalizer,
            )

            func.__sensei_routed_function__ = True
            func.__route__ = route

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

    def get(
            self,
            path: str,
            /, *,
            default_case: CaseConverter | None = None,
            query_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            response_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
            skip_preparer: bool = False,
    ) -> _RouteDecorator:
        """
        Create a route using the GET method.

        This decorator transforms a function into a routed function that sends a GET request
        to the specified path. Routed function handles parameter case conversion, argument validation, argument
        preparation, response finalizing.

        Args:
            path (str):
                The relative path of the route.
            default_case (CaseConverter, optional):
                Case converter for all parameters. Defaults to using the router's default.
            query_case (CaseConverter, optional):
                Case converter for query parameters. Defaults to using the router's default.
            cookie_case (CaseConverter, optional):
                Case converter for cookie parameters. Defaults to using the router's default.
            header_case (CaseConverter, optional):
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
        converters = CaseConverters(
            self,
            default_case=default_case,
            query_case=query_case,
            body_case=None,
            cookie_case=cookie_case,
            header_case=header_case,
            response_case=response_case,
        )

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
            default_case: CaseConverter | None = None,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            response_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
            skip_preparer: bool = False,
    ) -> _RouteDecorator:
        """
        Create a route using the POST method.

        This decorator transforms a function into a routed function that sends a POST request
        to the specified path. Routed function handles parameter case conversion, argument validation, argument
        preparation, response finalizing.

        Args:
            path (str):
                The relative path of the route.
            default_case (CaseConverter | None, optional):
                Case converter for all parameters. Defaults to using the router's default.
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
        converters = CaseConverters(
            self,
            default_case=default_case,
            query_case=query_case,
            body_case=body_case,
            cookie_case=cookie_case,
            header_case=header_case,
            response_case=response_case,
        )

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
            default_case: CaseConverter | None = None,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            response_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
            skip_preparer: bool = False,
    ) -> _RouteDecorator:
        """
        Create a route using the PATCH method.

        This decorator transforms a function into a routed function that sends a PATCH request
        to the specified path. Routed function handles parameter case conversion, argument validation, argument
        preparation, response finalizing.

        Args:
            path (str):
                The relative path of the route.
            default_case (CaseConverter | None, optional):
                Case converter for all parameters. Defaults to using the router's default.
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
        converters = CaseConverters(
            self,
            default_case=default_case,
            query_case=query_case,
            body_case=body_case,
            cookie_case=cookie_case,
            header_case=header_case,
            response_case=response_case,
        )

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
            default_case: CaseConverter | None = None,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            response_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
            skip_preparer: bool = False,
    ) -> _RouteDecorator:
        """
        Create a route using the PUT method.

        This decorator transforms a function into a routed function that sends a PUT request
        to the specified path. Routed function handles parameter case conversion, argument validation, argument
        preparation, response finalizing.

        Args:
            path (str):
                The relative path of the route.
            default_case (CaseConverter | None, optional):
                Case converter for all parameters. Defaults to using the router's default.
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
        converters = CaseConverters(
            self,
            default_case=default_case,
            query_case=query_case,
            body_case=body_case,
            cookie_case=cookie_case,
            header_case=header_case,
            response_case=response_case,
        )

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
            default_case: CaseConverter | None = None,
            query_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            response_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
            skip_preparer: bool = False,
    ) -> _RouteDecorator:
        """
        Create a route using the DELETE method.

        This decorator transforms a function into a routed function that sends a DELETE request
        to the specified path. Routed function handles parameter case conversion, argument validation, argument
        preparation, response finalizing.

        Args:
            path (str):
                The relative path of the route.
            default_case (CaseConverter | None, optional):
                Case converter for all parameters. Defaults to using the router's default.
            query_case (CaseConverter | None, optional):
                Case converter for query parameters. Defaults to using the router's default.
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
        converters = CaseConverters(
            self,
            default_case=default_case,
            query_case=query_case,
            body_case=None,
            cookie_case=cookie_case,
            header_case=header_case,
            response_case=response_case,
        )

        decorator = self._get_decorator(
            path=path,
            method="DELETE",
            case_converters=converters,
            skip_finalizer=skip_finalizer,
            skip_preparer=skip_preparer,
        )
        return decorator

    def head(
            self,
            path: str,
            /, *,
            default_case: CaseConverter | None = None,
            query_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            response_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
            skip_preparer: bool = False,
    ) -> _RouteDecorator:
        """
        Create a route using the HEAD method.

        This decorator transforms a function into a routed function that sends a HEAD request
        to the specified path. Routed function handles parameter case conversion, argument validation, argument
        preparation, response finalizing.

        Args:
            path (str):
                The relative path of the route.
            default_case (CaseConverter | None, optional):
                Case converter for all parameters. Defaults to using the router's default.
            query_case (CaseConverter | None, optional):
                Case converter for query parameters. Defaults to using the router's default.
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
            RoutedFunction: A routed function that sends a HEAD request according to the specified path and validates
            its arguments based on type annotations.

        Raises:
            pydantic_core.ValidationError: If type validation of arguments fails.
        """
        converters = CaseConverters(
            self,
            default_case=default_case,
            query_case=query_case,
            body_case=None,
            cookie_case=cookie_case,
            header_case=header_case,
            response_case=response_case,
        )

        decorator = self._get_decorator(
            path=path,
            method="HEAD",
            case_converters=converters,
            skip_finalizer=skip_finalizer,
            skip_preparer=skip_preparer,
        )
        return decorator

    def options(
            self,
            path: str,
            /, *,
            default_case: CaseConverter | None = None,
            query_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            response_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
            skip_preparer: bool = False,
    ) -> _RouteDecorator:
        """
        Create a route using the OPTIONS method.

        This decorator transforms a function into a routed function that sends a OPTIONS request
        to the specified path. Routed function handles parameter case conversion, argument validation, argument
        preparation, response finalizing.

        Args:
            path (str):
                The relative path of the route.
            default_case (CaseConverter | None, optional):
                Case converter for all parameters. Defaults to using the router's default.
            query_case (CaseConverter | None, optional):
                Case converter for query parameters. Defaults to using the router's default.
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
            RoutedFunction: A routed function that sends a OPTIONS request according to the specified path and validates
            its arguments based on type annotations.

        Raises:
            pydantic_core.ValidationError: If type validation of arguments fails.
        """
        converters = CaseConverters(
            self,
            default_case=default_case,
            query_case=query_case,
            body_case=None,
            cookie_case=cookie_case,
            header_case=header_case,
            response_case=response_case,
        )

        decorator = self._get_decorator(
            path=path,
            method="OPTIONS",
            case_converters=converters,
            skip_finalizer=skip_finalizer,
            skip_preparer=skip_preparer,
        )
        return decorator
