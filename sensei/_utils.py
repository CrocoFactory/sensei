import inspect
import re
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


def get_path_params(url: str) -> list[str]:
    pattern = r'\{(\w+)\}'

    parameters = re.findall(pattern, url)

    return parameters


def fill_path_params(url: str, values: dict[str, Any]) -> str:
    pattern = r'\{(\w+)\}'

    def replace_match(match: re.Match) -> str:
        param_name = match.group(1)
        return str(values.get(param_name, match.group(0)))

    new_url = re.sub(pattern, replace_match, url)

    return new_url