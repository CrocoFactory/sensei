from typing import Any
from sensei.types import IRateLimit


class _Attr:
    def __set_name__(self, owner: type, name: str) -> None:
        self._name = name

    def __get__(self, obj: object, owner: type) -> Any:
        return obj.__dict__[self._name]


class RateLimitAttr(_Attr):
    def __get__(self, obj: object, owner: type) -> IRateLimit:
        return super().__get__(obj, owner)

    def __set__(self, obj: object, value: IRateLimit) -> None:
        if value is None or isinstance(value, IRateLimit):
            obj.__dict__[self._name] = value
        else:
            raise TypeError(f'Value must implement {IRateLimit} interface')


class PortAttr(_Attr):
    def __get__(self, obj: object, owner: type) -> int:
        return super().__get__(obj, owner)

    def __set__(self, obj: object, value: int) -> None:
        if value is None or isinstance(value, int) and 1 <= value <= 65535:
            obj.__dict__[self._name] = value
        else:
            raise ValueError('Port must be between 1 and 65535')