import inspect
from typing import Any


def is_classmethod(obj: Any) -> bool:
    class _Temp:
        @classmethod
        def class_method(cls):
            pass

    type_ = type(_Temp.class_method)
    cond1 = isinstance(obj, type_)

    cond2 = cond3 = False
    if inspect.ismethod(obj):
        cond2 = isinstance(obj.__self__, type)
    else:
        cond3 = hasattr(obj, '__func__') and hasattr(obj, '__doc__') and hasattr(obj, '__name__')

    return cond1 or cond2 or cond3


def is_self_method(obj: Any) -> bool:
    return inspect.ismethod(obj) or is_classmethod(obj)