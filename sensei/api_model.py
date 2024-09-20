from typing import Any
from pydantic import BaseModel
from pydantic._internal._model_construction import ModelMetaclass
from ._internal import IRouter, RoutedMethod
from ._internal.tools.utils import bind_attributes
from ._utils import is_self_method


class _Namespace(dict):
    @staticmethod
    def _decorate_self_method(method: RoutedMethod) -> None:
        try:
            finalizer = method.__func__.finalizer
            initializer = method.__func__.initializer

            bind_attributes(method, finalizer, initializer)  # type: ignore
            method.__func__.__self__ = 'Hello'
        except AttributeError:
            pass

    def __setitem__(self, key, value):
        if is_self_method(value):
            self._decorate_self_method(value)
        super().__setitem__(key, value)


class _ModelMeta(ModelMetaclass):
    @classmethod
    def __prepare__(metacls, name, bases):
        return _Namespace()

    def __new__(cls, name, bases, dct):
        obj = super().__new__(cls, name, bases, dct)
        obj.__router__ = None

        return obj


class APIModel(BaseModel, metaclass=_ModelMeta):
    @staticmethod
    def __process_json__(json: dict[str, Any]) -> dict[str, Any]:
        return json

    def __str__(self):
        return f'{self.__class__.__name__}({super().__str__()})'
