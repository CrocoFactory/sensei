import inspect
from typing import Callable, TypeVar, Generic, Any
from pydantic import BaseModel
from sensei.client import Manager, AsyncClient, Client
from sensei._base_client import BaseClient
from ._endpoint import Endpoint, ResponseModel, ResponseTypes
from ._requester import Requester, Finalizer
from ..tools import HTTPMethod, args_to_kwargs

_Client = TypeVar('_Client', bound=BaseClient)
_RequestArgs = tuple[tuple[Any, ...], dict[str, Any]]


class _CallableHandler(Generic[_Client]):
    def __init__(
            self,
            *,
            path: str,
            method: HTTPMethod,
            func: Callable,
            default_host: str,
            request_args: _RequestArgs,
            manager: Manager[_Client] | None = None,
            finalizer: Finalizer | None = None
    ):
        self._func = func
        self._manager = manager
        self._method = method
        self._path = path
        self._default_host = default_host
        self._request_args = request_args
        self._temp_client: _Client | None = None
        self._finalizer = finalizer

    def __make_endpoint(self) -> Endpoint:
        params = {}
        sig = inspect.signature(self._func)

        for param in sig.parameters.values():
            if param.default and param.default is not inspect.Parameter.empty:
                params[param.name] = param.annotation, param.default
            else:
                params[param.name] = param.annotation

        return_type = sig.return_annotation if sig.return_annotation is not inspect.Signature.empty else None

        if return_type is not None and return_type not in ResponseTypes and type(return_type) != type(BaseModel):
            if self._finalizer is None:
                raise ValueError(f'Post Hook must be configured, if response is not derived from: {ResponseTypes}')
            else:
                return_type = dict

        endpoint = Endpoint(self._path, self._method, params=params, response=return_type)
        return endpoint

    def _make_requester(self, client: BaseClient) -> Requester:
        endpoint = self.__make_endpoint()
        requester = Requester(client, endpoint, finalizer=self._finalizer)
        return requester


class AsyncCallableHandler(_CallableHandler[AsyncClient], Generic[ResponseModel]):
    def __init__(
            self,
            *,
            method: HTTPMethod,
            path: str,
            func: Callable,
            default_host: str,
            request_args: _RequestArgs,
            manager: Manager[AsyncClient] | None = None,
            finalizer: Finalizer | None = None
    ):
        super().__init__(
            func=func,
            default_host=default_host,
            request_args=request_args,
            manager=manager,
            method=method,
            path=path,
            finalizer=finalizer
        )

    async def __aenter__(self) -> ResponseModel:
        manager = self._manager
        if manager is None or manager.empty():
            client = AsyncClient(host=self._default_host)
            await client.__aenter__()
            self._temp_client = client
        else:
            client = manager.get()

        requester = self._make_requester(client)
        kwargs = args_to_kwargs(self._func, *self._request_args[0], **self._request_args[1])
        return await requester.request(**kwargs)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if client := self._temp_client:
            await client.__aexit__(exc_type, exc_val, exc_tb)
            self._temp_client = None


class CallableHandler(_CallableHandler[Client], Generic[ResponseModel]):
    def __init__(
            self,
            *,
            method: HTTPMethod,
            path: str,
            func: Callable,
            default_host: str,
            request_args: _RequestArgs,
            manager: Manager[Client] | None = None,
            finalizer: Finalizer | None = None
    ):
        super().__init__(
            func=func,
            default_host=default_host,
            request_args=request_args,
            manager=manager,
            method=method,
            path=path,
            finalizer=finalizer
        )

    def __enter__(self) -> ResponseModel:
        manager = self._manager
        if manager is None or manager.empty():
            client = Client(host=self._default_host)
            client.__enter__()
            self._temp_client = client
        else:
            client = manager.get()

        requester = self._make_requester(client)
        kwargs = args_to_kwargs(self._func, *self._request_args[0], **self._request_args[1])
        return requester.request(**kwargs)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if client := self._temp_client:
            client.__exit__(exc_type, exc_val, exc_tb)
            self._temp_client = None
