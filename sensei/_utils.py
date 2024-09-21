import inspect
from typing import Any, TypeVar, Protocol

_T = TypeVar("_T")


class _NamedObj(Protocol):
    __name__ = ...


def is_classmethod(obj: Any) -> bool:
    return isinstance(obj, classmethod)


def is_staticmethod(obj: Any) -> bool:
    return isinstance(obj, staticmethod)


def is_instancemethod(obj: Any) -> bool:
    return inspect.isfunction(obj)


def is_selfmethod(obj: Any) -> bool:
    return is_classmethod(obj) or is_instancemethod(obj)


def is_method(obj: Any) -> bool:
    return is_selfmethod(obj) or is_staticmethod(obj)


def bind_attributes(obj: _T, *named_objects: tuple[_NamedObj]) -> _T:
    for named_obj in named_objects:
        setattr(obj, named_obj.__name__, named_obj)

    return obj
