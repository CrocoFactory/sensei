from __future__ import annotations

from abc import abstractmethod, ABC
from enum import Enum
from typing import Protocol, TypeVar, Callable, Any, Mapping, Union, Awaitable, Literal, get_args, Optional

from httpx import URL
from pydantic import validate_call, BaseModel, ConfigDict
from typing_extensions import Self, TypeGuard

from sensei.client import Manager
from sensei.types import IRateLimit, Json
from .args import Args
from ..tools import MethodType, identical, HTTPMethod

CaseConverter = Callable[[str], str]

_RT = TypeVar('_RT')


class RoutedMethod(Protocol):
    __func__: RoutedFunction
    __name__: str
    __doc__: str
    __route__: IRoute


class RoutedFunction(Callable[..., _RT]):
    """
    Function produced by routed decorators, such as:

    * `@router.get`
    * `@router.post`
    * `@router.put`
    * `@router.delete`
    * `@router.patch`
    * `@router.head`
    * `@router.options`

    Example:
        ```python
        from sensei import Router

        router = Router('https://api.example.com')

        @router.get('/users')
        def get_user(id: int) -> User:
            pass
        ```
    """
    def __call__(self, *args, **kwargs) -> _RT:
        ...

    def prepare(self, preparer: Preparer | None = None) -> Preparer:
        """
        Attach preparer to the routed function. Preparer is a function that takes an instance of `Args` as the argument
        and returns the modified. Preparers are used for request preparation. That means adding or changing arguments
        before request. Can be represented as **async function**.

        Preparers are executed after internal argument parsing. So, all request parameters are available in
        `Args` model within a preparer.

        Example:
            ```python
            from sensei import APIModel, format_str, Router, Args
            from pydantic import NonNegativeInt, EmailStr

            router = Router('https://api.example.com')

            class User(APIModel):
                id: NonNegativeInt
                email: EmailStr
                nickname: str

                @router.patch('/users/{id_}')
                def update(
                        self,
                        name: str,
                        job: str
                ) -> None:
                    pass

                @update.prepare
                def _update_in(self, args: Args) -> Args:
                    args.url = format_str(args.url, {'id_': self.id})
                    return args
            ```

        Args:
            preparer (Preparer):
                Function that takes an instance of `Args` as the argument and returns the modified

        Returns (Preparer): Function that was passed
        """
        ...

    def finalize(self, finalizer: ResponseFinalizer | None = None) -> ResponseFinalizer:
        """
        Attach response finalizer to the routed function. Response Finalizer is a function that takes an instance of
        `httpx.Response` as the argument and returns the result of calling the associated routed function.
        The return value must be of the same type as the routed function. Can be represented as **async function**.

        Response Finalizers are used for response transformation, which can't be performed automatically if you set a
        corresponding response type from the category of automatically handled.

        Example:
            ```python
            from sensei import Router, APIModel, Form
            from pydantic import EmailStr
            from typing import Annotated
            from httpx import Response

            router = Router('https://api.example.com')

            class UserCredentials(APIModel):
                email: EmailStr
                password: str

            @router.post('/register')
            def sign_up(user: Annotated[UserCredentials, Form(embed=False)]) -> str:
                pass

            @sign_up.finalize
            def _sign_up_out(response: Response) -> str:
                print(f'Finalizing response for request {response.request.url}')
                return response.json()['token']


            token = sign_up(UserCredentials(
                email='john@example.com',
                password='secret_password')
            )
            print(f'JWT token: {token}')
            ```

        Args:
            finalizer (ResponseFinalizer):
                Function that takes an instance of `httpx.Response` as the argument and returns the result of calling
                the routed function. The return value must be of the same type as the routed function.

        Returns:
            Function that was passed
        """
        ...

    __method_type__: MethodType
    __name__: str
    __doc__: str
    __route__: IRoute
    __sensei_routed_function__: bool = True


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
    def base_url(self) -> URL:
        pass

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


class IRoute(ABC):
    @property
    @abstractmethod
    def path(self) -> str:
        pass

    @property
    @abstractmethod
    def method(self) -> HTTPMethod:
        pass

    @property
    @abstractmethod
    def is_async(self) -> bool:
        pass

    @property
    @abstractmethod
    def method_type(self) -> MethodType:
        pass

    @method_type.setter
    @abstractmethod
    def method_type(self, value: MethodType):
        pass

    @property
    @abstractmethod
    def hooks(self) -> Hooks:
        pass

    @abstractmethod
    def finalize(self, func: ResponseFinalizer | None = None) -> Callable:
        pass

    @abstractmethod
    def prepare(self, func: Preparer | None = None) -> Callable:
        pass


_KT = TypeVar('_KT')
_VT = TypeVar('_VT')

ConverterName = Literal['default_case', 'query_case', 'body_case', 'cookie_case', 'header_case', 'response_case']


class _MappingGetter(dict[_KT, _VT]):
    def __init__(
            self,
            dict_getter: Callable[[], dict[_KT, _VT]]
    ):
        __dict = dict_getter()
        super().__init__(__dict)
        self.__getter = dict_getter

    def __getitem__(self, item: _KT) -> _VT:
        return self.__getter()[item]

    def __setitem__(self, key: _KT, value: _VT) -> None:
        raise TypeError(f'{self.__class__.__name__} does not support item assignment')


class CaseConverters(_MappingGetter[ConverterName, CaseConverter]):
    def __init__(
            self,
            router: IRouter,
            *,
            default_case: CaseConverter | None = None,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            response_case: CaseConverter | None = None,
    ):
        self.__router = router
        self._defaults = {
            'query_case': query_case,
            'body_case': body_case,
            'cookie_case': cookie_case,
            'header_case': header_case,
            'response_case': response_case,
        }

        self._sub_defaults = {}

        self._default_case = default_case or router.default_case

        super().__init__(self.__getter)

    @property
    @validate_call(validate_return=True)
    def defaults(self) -> dict[ConverterName, Optional[CaseConverter]]:
        return self._sub_defaults

    @defaults.setter
    @validate_call(validate_return=True)
    def defaults(self, value: dict[ConverterName, CaseConverter]) -> None:
        self._sub_defaults = value

    def __setitem__(self, key, value):
        is_default = key == 'default_case'
        if key not in self._defaults and not is_default:
            raise KeyError(f'{key} is not a valid key')
        else:
            if is_default:
                self._default_case = value
            else:
                self._defaults[key] = value

    def __getitem__(self, item: ConverterName) -> CaseConverter:
        converter = super().__getitem__(item)
        if converter is None:
            converter = identical

        return converter

    def __getter(self) -> dict[str, CaseConverter]:
        router = self.__router
        converters = self._defaults.copy()
        default = self._default_case

        for key, converter in converters.items():
            converter = converter or self.defaults.get(key)
            if converter is None:
                router_converter = getattr(router, f'{key}')
                converters[key] = default if router_converter is None else router_converter
            else:
                converters[key] = converter

        return converters


class ModelHook(Enum):
    JSON_FINALIZER = "__finalize_json__"
    ARGS_PREPARER = "__prepare_args__"

    DEFAULT_CASE = "__default_case__"
    QUERY_CASE = "__query_case__"
    BODY_CASE = "__body_case__"
    COOKIE_CASE = "__cookie_case__"
    HEADER_CASE = "__header_case__"
    RESPONSE_CASE = "__response_case__"

    @classmethod
    def values(cls) -> list[str]:
        return [member.value for member in cls]

    def is_case_hook(self) -> bool:
        return self.value.endswith("_case__")


class Hooks(BaseModel):
    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)

    prepare_args: Preparer = identical
    post_preparer: Preparer = identical
    finalize_json: JsonFinalizer = identical
    response_finalizer: Optional[ResponseFinalizer] = None
    case_converters: CaseConverters

    @staticmethod
    def _is_converter_name(name: str) -> TypeGuard[ConverterName]:
        return name in get_args(ConverterName)

    @validate_call(validate_return=True)
    def set_model_hooks(self, hooks: dict[ModelHook, Callable]) -> None:
        case_hooks = {}
        for key, value in hooks.items():
            stripped = key.value[2:-2]
            if key.is_case_hook():
                if self._is_converter_name(stripped):
                    case_hooks[stripped] = value
                else:
                    raise ValueError('Unsupported case hook')
            else:
                setattr(self, stripped, value)

        self.case_converters.defaults = case_hooks


Preparer = Callable[[Args], Union[Args, Awaitable[Args]]]
ResponseFinalizer = Callable[[IResponse], Any]
JsonFinalizer = Callable[[Json], Json]
