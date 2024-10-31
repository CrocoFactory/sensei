import inspect
import sys
from collections import OrderedDict
from functools import wraps
from typing import Any, get_args, Callable, TypeVar, Optional, Protocol

from pydantic import BaseModel, ConfigDict
from pydantic._internal._model_construction import ModelMetaclass

from sensei._utils import placeholders
from .types import HTTPMethod, MethodType

_T = TypeVar("_T")


def make_model(
        model_name: str,
        model_args: dict[str, Any],
        model_config: Optional[ConfigDict] = None,
) -> type[BaseModel]:
    annotations = {}
    defaults = {}
    for key, arg in model_args.items():
        if isinstance(arg, (tuple, list)):
            annotations[key] = arg[0]
            if len(arg) == 2:
                defaults[key] = arg[1]
        else:
            annotations[key] = arg

    namespace = {
        '__module__': sys.modules[__name__],
        '__qualname__': model_name,
        '__annotations__': annotations,
        **defaults
    }

    if model_config:
        namespace['model_config'] = model_config

    model: type[BaseModel] = ModelMetaclass(  # type: ignore
        model_name,
        (BaseModel,),
        namespace
    )
    return model


def split_params(url: str, params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    path_params_names = placeholders(url)

    path_params = {}
    for path_param_name in path_params_names:
        if (value := params.get(path_param_name)) is not None:
            path_params[path_param_name] = value
            del params[path_param_name]

    return params, path_params


def accept_body(method: HTTPMethod) -> bool:
    if method not in {'DELETE', 'GET', 'TRACE', 'OPTIONS', 'HEAD'}:
        return True
    else:
        return False


def validate_method(method: HTTPMethod) -> bool:
    methods = get_args(HTTPMethod)
    if method not in methods:
        raise ValueError(f'Invalid HTTP method "{method}". '
                         f'Standard HTTP methods defined by the HTTP/1.1 protocol: {methods}')
    else:
        return True


def args_to_kwargs(func: Callable, *args, **kwargs) -> OrderedDict[str, Any]:
    sig = inspect.signature(func)

    bound_args = sig.bind_partial(*args, **kwargs)
    bound_args.apply_defaults()

    return OrderedDict(bound_args.arguments)


def set_method_type(func: Callable):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not args:
            method_type = MethodType.STATIC
        else:
            first_arg = args[0]

            func_name = getattr(first_arg, func.__name__, None)
            is_first_self = hasattr(first_arg, func.__name__) and getattr(func_name, '__self__', None) is first_arg

            if is_first_self:
                if inspect.isclass(first_arg):
                    method_type = MethodType.CLASS
                else:
                    method_type = MethodType.INSTANCE
            else:
                method_type = MethodType.STATIC

        setattr(wrapper, '__method_type__', method_type)

        return func(*args, **kwargs)

    return wrapper


def identical(value: _T) -> _T:
    return value


def is_coroutine_function(func: Callable) -> bool:
    return (inspect.iscoroutinefunction(func) or
            (hasattr(func, '__wrapped__') and inspect.iscoroutinefunction(func.__wrapped__)))


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
