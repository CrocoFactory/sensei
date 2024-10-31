from __future__ import annotations

from abc import abstractmethod, ABC
from typing import Protocol, TypeVar, Callable, Any, Mapping, Union, Awaitable

from pydantic import BaseModel, Field
from typing_extensions import Self

from sensei.client import Manager
from sensei.types import IRateLimit
from sensei.types import Json
from ..tools import MethodType

CaseConverter = Callable[[str], str]


class Args(BaseModel):
    """
    Model used in preparers as input and output argument. Stores request arguments

    Attributes:
        url (str): URL to which the request will be made.
        params (dict[str, Any]): Dictionary of query parameters to be included in the URL.
        data (dict[str, Any]): Dictionary of payload for the request body.
        json_ (Json): JSON payload for the request body.
                                The field is aliased as 'json' and defaults to an empty dictionary.
        files (dict[str, Any]): File payload for the request body.
        headers (dict[str, Any]): Dictionary of HTTP headers to be sent with the request.
        cookies (dict[str, Any]): Dictionary of cookies to be included in the request.
    """
    url: str
    params: dict[str, Any] = {}
    json_: Json = Field({}, alias="json")
    data: Any = {}
    headers: dict[str, Any] = {}
    cookies: dict[str, Any] = {}
    files: dict[str, Any] = {}

    def model_dump(self, *args, **kwargs) -> dict[str, Any]:
        data = super().model_dump(*args, exclude={'files'}, **kwargs)
        data['files'] = self.files
        return self._exclude_none(data)

    @classmethod
    def _exclude_none(cls, data: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(data, dict):
            return data
        return {k: cls._exclude_none(v) for k, v in data.items() if v is not None}


class RoutedFunction(Protocol):
    def __call__(self, *args, **kwargs):
        ...

    def prepare(self, preparer: Preparer | None = None) -> Preparer:
        ...

    def finalize(self, finalizer: ResponseFinalizer | None = None) -> ResponseFinalizer:
        ...

    __method_type__: MethodType
    __name__: str
    __doc__: str
    __routed__: bool = True


class RoutedMethod(Protocol):
    __func__: RoutedFunction
    __name__: str
    __doc__: str


class _RoutedModel(Protocol):
    __router__ = ...
    __finalize_json__: JsonFinalizer
    __prepare_args__: Preparer

    __default_case__: CaseConverter
    __query_case__: CaseConverter
    __body_case__: CaseConverter
    __cookie_case__: CaseConverter
    __header_case__: CaseConverter
    __response_case__: CaseConverter


RoutedModel = TypeVar("RoutedModel", bound=_RoutedModel)


class IRequest(Protocol):
    @property
    def headers(self) -> Mapping[str, Any]:
        pass

    @property
    def method(self) -> str:
        pass

    @property
    def url(self) -> Any:
        pass


class IResponse(Protocol):
    __slots__ = ()

    def __await__(self):
        pass

    def json(self) -> Json:
        pass

    def raise_for_status(self) -> Self:
        pass

    @property
    def request(self) -> IRequest:
        pass

    @property
    def text(self) -> str:
        pass

    @property
    def status_code(self) -> int:
        pass

    @property
    def content(self) -> bytes:
        pass

    @property
    def headers(self) -> Mapping[str, Any]:
        pass


class IRouter(ABC):
    __slots__ = ()

    @property
    @abstractmethod
    def manager(self) -> Manager:
        pass

    @property
    @abstractmethod
    def port(self) -> int:
        pass

    @property
    @abstractmethod
    def rate_limit(self) -> IRateLimit:
        pass

    @abstractmethod
    def model(self, model_obj: RoutedModel | None) -> RoutedModel:
        pass

    @abstractmethod
    def get(
            self,
            path: str,
            /, *,
            query_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
    ) -> RoutedFunction:
        pass

    @abstractmethod
    def post(
            self,
            path: str,
            /, *,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
    ) -> RoutedFunction:
        pass

    @abstractmethod
    def patch(
            self,
            path: str,
            /, *,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
    ) -> RoutedFunction:
        pass

    @abstractmethod
    def put(
            self,
            path: str,
            /, *,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
    ) -> RoutedFunction:
        pass

    @abstractmethod
    def delete(
            self,
            path: str,
            /, *,
            query_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
    ) -> RoutedFunction:
        pass

    @abstractmethod
    def options(
            self,
            path: str,
            /, *,
            query_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
    ) -> RoutedFunction:
        pass

    @abstractmethod
    def head(
            self,
            path: str,
            /, *,
            query_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
    ) -> RoutedFunction:
        pass

    @property
    @abstractmethod
    def default_case(self) -> CaseConverter:
        pass

    @property
    @abstractmethod
    def query_case(self) -> CaseConverter:
        pass

    @property
    @abstractmethod
    def body_case(self) -> CaseConverter:
        pass

    @property
    @abstractmethod
    def cookie_case(self) -> CaseConverter:
        pass

    @property
    @abstractmethod
    def header_case(self) -> CaseConverter:
        pass

    @property
    @abstractmethod
    def response_case(self) -> CaseConverter:
        pass


ResponseModel = TypeVar(
    'ResponseModel',
    type[BaseModel],
    str,
    dict,
    bytes,
    list[dict],
    BaseModel,
    list[BaseModel],
)

RESPONSE_TYPES = ResponseModel.__constraints__


Preparer = Callable[[Args], Union[Args, Awaitable[Args]]]
ResponseFinalizer = Callable[[IResponse], Union[ResponseModel, Awaitable[ResponseModel]]]
JsonFinalizer = Callable[[Json], Json]
