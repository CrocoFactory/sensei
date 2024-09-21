import functools
from typing import Any
from pydantic import BaseModel
from pydantic._internal._model_construction import ModelMetaclass
from ._internal import RoutedMethod
from ._internal.tools.utils import bind_attributes
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
        elif key == '__finalize_json__' and is_selfmethod(value):
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
    @staticmethod
    def __finalize_json__(json: dict[str, Any]) -> dict[str, Any]:
        return json

    def __str__(self):
        return f'{self.__class__.__name__}({super().__str__()})'
