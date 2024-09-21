import inspect
from typing import Any


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
