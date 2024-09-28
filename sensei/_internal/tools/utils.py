import sys
import inspect
from functools import wraps
from pydantic import BaseModel
from collections import OrderedDict
from sensei._utils import placeholders
from typing import Any, get_args, Callable, TypeVar
from .types import HTTPMethod, MethodType
from pydantic._internal._model_construction import ModelMetaclass

_T = TypeVar("_T")


def make_model(model_name: str, model_args: dict[str, Any]) -> type[BaseModel]:
    annotations = {}
    defaults = {}
    for key, arg in model_args.items():
        if isinstance(arg, (tuple, list)):
            annotations[key] = arg[0]
            if len(arg) == 2:
                defaults[key] = arg[1]
        else:
            annotations[key] = arg

    model: type[BaseModel] = ModelMetaclass(  # type: ignore
        model_name,
        (BaseModel,),
        {
            '__module__': sys.modules[__name__],
            '__qualname__': model_name,
            '__annotations__': annotations,
            **defaults
        }
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


def is_safe_method(method: HTTPMethod) -> bool:
    if method in {'GET', 'TRACE', 'OPTIONS', 'HEAD'}:
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
