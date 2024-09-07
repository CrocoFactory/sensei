import re
import sys
import inspect
from pydantic import BaseModel
from typing import Any, get_args, Callable
from .types import HTTPMethod
from pydantic._internal._model_construction import ModelMetaclass


def make_model(model_name: str, model_args: dict[str, Any]) -> type[BaseModel]:
    if model_args:
        annotations = {}
        defaults = {}
        for key, arg in model_args.items():
            if isinstance(arg, tuple | list):
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


def _path_params(url: str) -> list[str]:
    pattern = r'\{(\w+)\}'

    parameters = re.findall(pattern, url)

    return parameters


def split_params(url: str, params: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    path_params_names = _path_params(url)

    path_params = {}
    for path_param_name in path_params_names:
        path_params[path_param_name] = params[path_param_name]
        del params[path_param_name]

    return params, path_params


def fill_path_params(url: str, values: dict[str, Any]) -> str:
    pattern = r'\{(\w+)\}'

    def replace_match(match: re.Match) -> str:
        param_name = match.group(1)
        return str(values.get(param_name, match.group(0)))

    new_url = re.sub(pattern, replace_match, url)

    return new_url


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


def args_to_kwargs(func: Callable, *args, **kwargs) -> dict[str, Any]:
    sig = inspect.signature(func)

    bound_args = sig.bind_partial(*args, **kwargs)
    bound_args.apply_defaults()

    return dict(bound_args.arguments)
