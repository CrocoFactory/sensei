from typing import Any, Callable

from pydantic import BaseModel
from pydantic._internal._model_construction import ModelMetaclass
from typing_extensions import TypeGuard

from sensei.types import Json
from ._types import RoutedMethod, ModelHook, RoutedFunction
from .args import Args
from ..tools import is_staticmethod, is_classmethod, is_instancemethod, bind_attributes, is_method


class _Namespace(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._routed_functions = set()

    @property
    def routed_functions(self) -> set[RoutedFunction]:
        return self._routed_functions

    @staticmethod
    def _decorate_method(method: RoutedMethod) -> None:
        preparer = method.__func__.prepare
        finalizer = method.__func__.finalize

        bind_attributes(method, finalizer, preparer)  # type: ignore

    @staticmethod
    def _is_routed_function(obj: Any) -> TypeGuard[RoutedMethod]:
        cond = False
        if is_method(obj):
            if is_staticmethod(obj) or is_classmethod(obj):
                obj = obj.__func__
            cond = getattr(obj, '__sensei_routed_function__', None) is True
        return cond

    def __setitem__(self, key: Any, value: Any):
        if self._is_routed_function(value):
            if is_staticmethod(value) or is_classmethod(value):
                self._decorate_method(value)
                self._routed_functions.add(value.__func__)
            else:
                self._routed_functions.add(value)
        elif key in ModelHook.values():
            if is_instancemethod(value):
                raise ValueError(f'Class hook {value.__name__} cannot be instance method')

        super().__setitem__(key, value)


class _ModelBase(BaseModel):
    @staticmethod
    def __finalize_json__(json: Json) -> Json:
        """
        Hook used to finalize the JSON response. It's applied for each routed method, associated with the model
        The final value must be JSON serializable. Can be represented as **async function**.

        JSON finalizer is used for JSON response transformation before internal or user-defined response finalizing.

        Example:
            ```python
            from sensei import Router, APIModel, Path
            from typing import Any, Annotated


            router = Router('https://reqres.in/api')


            class User(APIModel):
                email: str
                id: int
                first_name: str
                last_name: str
                avatar: str

                @staticmethod
                def __finalize_json__(json: dict[str, Any]) -> dict[str, Any]:
                    return json['data']

                @classmethod
                @router.get('/users/{id_}')
                def get(cls, id_: Annotated[int, Path()]) -> "User":
                    pass
            ```

        Args:
            json (Json): The original JSON response.

        Returns:
            Json: The finalized JSON response.
        """
        return json

    @staticmethod
    def __prepare_args__(args: Args) -> Args:
        """
        Hook used to prepare the arguments for the request before it is sent. It's applied for
        each routed method, associated with the model. The final value must be an instance of `Args`.
        Can be represented as **async function**.

        Preparer is executed after internal argument parsing. So, all request parameters are available in
        `Args` model within a preparer.

        Example:
            ```python
            from sensei import APIModel, Router, Args, Path

            class Context:
                token: str

            router = Router('https://api.example.com')


            class User(APIModel):
                email: str
                id: int
                first_name: str
                last_name: str
                avatar: str

                @staticmethod
                def __prepare_args__(args: Args) -> Args:
                    args.headers['Authorization'] = f'Bearer {Context.token}'
                    return args

                @classmethod
                @router.get('/users/{id_}')
                def get(cls, id_: Annotated[int, Path()]) -> "User":
                    pass
            ```

        Args:
            args (Args): The original arguments.

        Returns:
            Args: The prepared arguments.
        """
        return args

    @staticmethod
    def __default_case__(s: str) -> str:
        """
        Hook used to convert the case of all parameters.

        Args:
            s (str): The original string.

        Returns:
            str: The converted string.
        """
        return s

    @staticmethod
    def __query_case__(s: str) -> str:
        """
        Hook used to convert the case of query parameters.

        Example:
            ```python
            from sensei import Router, APIModel, Path, camel_case
            from typing import Any, Annotated


            router = Router('https://reqres.in/api')


            class User(APIModel):
                email: str
                id: int
                first_name: str
                last_name: str
                avatar: str

                @staticmethod
                def __query_case__(s: str) -> str:
                    return camel_case(s)

                @classmethod
                @router.get('/users/{id_}')
                def get(cls, id_: Annotated[int, Path()]) -> "User":
                    pass
            ```

        Args:
            s (str): The original string.

        Returns:
            str: The converted string.
        """
        return s

    @staticmethod
    def __body_case__(s: str) -> str:
        """
        Hook used to convert the case of body.

        Args:
            s (str): The original string.

        Returns:
            str: The converted string.
        """
        return s

    @staticmethod
    def __cookie_case__(s: str) -> str:
        """
        Hook used to convert the case of cookies.

        Args:
            s (str): The original string.

        Returns:
            str: The converted string.
        """
        return s

    @staticmethod
    def __header_case__(s: str) -> str:
        """
        Hook used to convert the case of headers.

        Args:
            s (str): The original string.

        Returns:
            str: The converted string.
        """
        return s

    @staticmethod
    def __response_case__(s: str) -> str:
        """
        Hook used to convert the case of JSON response keys.

        Args:
            s (str): The original string.

        Returns:
            str: The converted string.
        """
        return s

    def __str__(self):
        """
        Get the string representation of the model. Wraps `pydantic` representation through the class name and parenthesis

        Example:
            ```python
            @router.get('/pokemon/{name}')
            def get_pokemon(name: Annotated[str, Path(max_length=300)]) -> Pokemon:
                pass


            pokemon = get_pokemon(name="pikachu")
            print(pokemon)
            ```

            ```text
            Pokemon(name='pikachu' id=25 height=4 weight=60)
            ```


        Returns:
            str: String representation of the model
        """
        return f'{self.__class__.__name__}({super().__str__()})'


class _ModelMeta(ModelMetaclass):
    @classmethod
    def __prepare__(metacls, name, bases):
        namespace = _Namespace()
        return namespace

    def __new__(
            cls,
            cls_name: str,
            bases: tuple[type[Any], ...],
            namespace: _Namespace,
    ):
        obj = super().__new__(cls, cls_name, bases, namespace)

        hooks = cls.__collect_hooks(obj)

        routed_functions = namespace.routed_functions
        for fun in routed_functions:
            fun.__route__.hooks.set_model_hooks(hooks)

        obj.__router__ = None

        return obj

    @staticmethod
    def __collect_hooks(obj: object) -> dict[ModelHook, Callable]:
        hooks = {}
        for value in ModelHook.values():
            hook = getattr(obj, value, None)

            is_defined = hook is not getattr(_ModelBase, value, None)
            if hook and is_defined:
                hooks[value] = hook
        return hooks  # type: ignore


class APIModel(_ModelBase, metaclass=_ModelMeta):
    """
    Base class used to define models for structuring API responses.
    There is the OOP style of making Sensei models when an `APIModel` class performs both validation and making requests
    through its routed methods. This style is called **Routed Model**. To use this style, you need to implement a model derived
    from `APIModel` and add inside routed methods.

    You can apply the same techniques as for [`pydantic.BaseModel`](https://docs.pydantic.dev/2.9/concepts/models/){.external-link}

    Import it directly from Sensei:

    ```python
    from sensei import APIModel
    ```

    !!! example
        === "Simple Model"
            ```python
            from typing import Annotated, Any
            from sensei import Router, Path, APIModel

            router = Router('https://example.com/api')

            class User(APIModel):
                 email: str
                 id: int
                 first_name: str
                 last_name: str
                 avatar: str

            @router.get('/users/{id_}')
            def get_user(id_: Annotated[int, Path()]) -> User:
                pass

            user = get_user(1)
            print(user.email)
            ```

        === "Routed Model"
            ```python
            from typing import Annotated, Any
            from sensei import Router, Path, APIModel

            router = Router('https://example.com/api')

            class User(APIModel):
                 email: str
                 id: int
                 first_name: str
                 last_name: str
                 avatar: str

                 @classmethod
                 @router.get('/users/{id_}')
                 def get(cls, id_: Annotated[int, Path()]) -> "User":
                     pass

            user = User.get(1)
            print(user.email)
            ```
    """
    pass
