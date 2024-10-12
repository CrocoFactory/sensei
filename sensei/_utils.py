import inspect
import re
from typing import Any, TypeVar, Protocol
from urllib.parse import urlparse, urlunparse

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


def placeholders(url: str) -> list[str]:
    """
    Extracts placeholder names from a string.

    This function searches the string for placeholders in the format `{param_name}`
    and returns a list of all parameter names found in the string.

    Args:
        url (str): The string containing placeholders in the format `{param_name}`.

    Returns:
        list[str]: A list of placeholder names found in the string. Each name is a string
                   corresponding to the `param_name` inside `{}` brackets.

    Example:
        >>> url = "https://example.com/users/{user_id}/posts/{post_id}"
        >>> result = placeholders(url)
        ["user_id", "post_id"]
    """
    pattern = r'\{(\w+)\}'

    parameters = re.findall(pattern, url)

    return parameters


def format_str(s: str, values: dict[str, Any], ignore_missed: bool = False) -> str:
    """
    Replaces placeholders in the string with corresponding values from the provided dictionary.

    This function searches the string for placeholders in the format `{param_name}` and replaces
    them with the value from the `values` dictionary where the key is `param_name`. If no corresponding
    value is found for a placeholder, it raises KeyError

    Args:
        s (str): String containing placeholders in the format `{param_name}`.
        values (dict[str, Any]): Dictionary where keys are parameter names and values are
                                 used to replace the placeholders in the URL.
        ignore_missed: Whether to ignore missed values

    Returns:
        str: String with placeholders replaced by corresponding values from the `values` dictionary.

    Raises
        KeyError: If no corresponding value is found for a placeholder

    Example:
        >>> url = "https://example.com/users/{user_id}/posts/{post_id}"
        >>> values = {"user_id": 42, "post_id": 1001}
        >>> format_str(url, values)
        https://example.com/users/42/posts/1001
    """
    try:
        return s.format(**values)
    except KeyError:
        if not ignore_missed:
            raise
        else:
            keys = placeholders(s)
            values = values | {k: f'{"{"+ k +"}"}' for k in keys}
            return s.format(**values)


def normalize_url(url: str) -> str:
    parsed = urlparse(url)

    path = parsed.path.rstrip('/') if len(parsed.path) == 1 or not parsed.path.endswith('//') else parsed.path

    normalized_url = urlunparse(parsed._replace(path=path))
    return normalized_url  # type: ignore


def get_base_url(host: str, port: int) -> str:
    host = normalize_url(host)
    if 'port' in placeholders(host):
        api_url = format_str(host, {'port': port})
    elif port is not None:
        api_url = f'{host}:{port}'
    else:
        api_url = host

    return api_url
