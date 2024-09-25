import functools
from typing import Any
from pydantic import BaseModel
from pydantic._internal._model_construction import ModelMetaclass
from ._internal import RoutedMethod, Hook, Args
from ._utils import bind_attributes
from ._utils import is_staticmethod, is_classmethod, is_selfmethod


class _Namespace(dict):
    @staticmethod
    def _decorate_method(method: RoutedMethod) -> None:
        try:
            preparer = method.__func__.prepare
            finalizer = method.__func__.finalize

            bind_attributes(method, finalizer, preparer)  # type: ignore
        except AttributeError:
            pass

    def __setitem__(self, key: Any, value: Any):
        if is_staticmethod(value) or is_classmethod(value):
            self._decorate_method(value)
        elif key in Hook.values() and is_selfmethod(value):
            value = functools.partial(value, None)

        super().__setitem__(key, value)


class _ModelMeta(ModelMetaclass):
    @classmethod
    def __prepare__(metacls, name, bases):
        return _Namespace()

    def __new__(
            cls,
            cls_name: str,
            bases: tuple[type[Any], ...],
            namespace: dict[str, Any],
    ):
        obj = super().__new__(cls, cls_name, bases, namespace)
        obj.__router__ = None

        return obj


class APIModel(BaseModel, metaclass=_ModelMeta):
    """
    Base class for creating Sensei API models. Don`t confuse it with Pydantic BaseModel, it`s used simultaneously
    for validating output data and provide "routed" functions.

    But usage rools are the same with BaseModel
    Usage docs: https://docs.pydantic.dev/2.9/concepts/models/

    To make the proper class, decorate it with @router.model. Avoiding this requirements will lead you to the issues.

    Examples:
        >>> from typing import Annotated, Any, Self
        >>> from sensei import Router, Query, Path, APIModel
        >>>
        >>> router = Router('https://reqres.in/api')
        >>>
        >>> @router.model()
        >>> class User(APIModel):
        >>>     email: str
        >>>     id: int
        >>>     first_name: str
        >>>     last_name: str
        >>>     avatar: str
        >>>
        >>>     @classmethod
        >>>     @router.get('/users/{id_}')
        >>>     def get(cls, id_: Annotated[int, Path(alias='id')]) -> Self:
        >>>         ...
    """

    @staticmethod
    def __finalize_json__(json: dict[str, Any]) -> dict[str, Any]:
        """
        Finalize the JSON response.

        This hook is used to finalize the JSON response. The final value must be JSON serializable.

        Args:
            json (dict[str, Any]): The original JSON response.

        Returns:
            dict[str, Any]: The finalized JSON response.
        """
        return json

    @staticmethod
    def __prepare_args__(args: Args) -> Args:
        """
        Prepare the arguments for the request.

        This hook is used to prepare the arguments for the request before it is sent.
        The final value must be an instance of `Args`.

        Args:
            args (Args): The original arguments.

        Returns:
            Args: The prepared arguments.
        """
        return args

    @staticmethod
    def __query_case__(s: str) -> str:
        """
        Convert the case of query parameters.

        This hook is used to convert the case of query parameters to the desired format.

        Args:
            s (str): The original query parameter string.

        Returns:
            str: The converted query parameter string.
        """
        return s

    @staticmethod
    def __body_case__(s: str) -> str:
        """
        Convert the case of body parameters.

        This hook is used to convert the case of body parameters to the desired format.

        Args:
            s (str): The original body parameter string.

        Returns:
            str: The converted body parameter string.
        """
        return s

    @staticmethod
    def __cookie_case__(s: str) -> str:
        """
        Convert the case of cookie parameters.

        This hook is used to convert the case of cookie parameters to the desired format.

        Args:
            s (str): The original cookie parameter string.

        Returns:
            str: The converted cookie parameter string.
        """
        return s

    @staticmethod
    def __header_case__(s: str) -> str:
        """
        Convert the case of header parameters.

        This hook is used to convert the case of header parameters to the desired format.

        Args:
            s (str): The original header parameter string.

        Returns:
            str: The converted header parameter string.
        """
        return s

    def __str__(self):
        return f'{self.__class__.__name__}({super().__str__()})'
