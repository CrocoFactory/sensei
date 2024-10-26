from __future__ import annotations

from typing import TypeVar, Callable, Literal

from sensei._internal.tools import identical
from ._types import CaseConverter, IRouter

_KT = TypeVar('_KT')
_VT = TypeVar('_VT')

_Keys = Literal['query_case', 'body_case', 'cookie_case', 'header_case', 'response_case']


class _MappingGetter(dict[_KT, _VT]):
    def __init__(
            self,
            dict_getter: Callable[[], dict[_KT, _VT]]
    ):
        __dict = dict_getter()
        super().__init__(__dict)
        self.__getter = dict_getter

    def __getitem__(self, item: _KT) -> _VT:
        return self.__getter()[item]

    def __setitem__(self, key: _KT, value: _VT) -> None:
        raise TypeError(f'{self.__class__.__name__} does not support item assignment')


class CaseConverters(_MappingGetter[_Keys, CaseConverter]):
    def __init__(
            self,
            router: IRouter,
            *,
            default_case: CaseConverter | None = None,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            response_case: CaseConverter | None = None,
    ):
        self.__router = router
        self._defaults = {
            'query_case': query_case,
            'body_case': body_case,
            'cookie_case': cookie_case,
            'header_case': header_case,
            'response_case': response_case,
        }

        self._default_case = default_case or router.default_case

        super().__init__(self.__getter)

    def __getitem__(self, item: _Keys) -> CaseConverter:
        converter = super().__getitem__(item)
        if converter is None:
            converter = identical

        return converter

    def __getter(self) -> dict[str, CaseConverter]:
        router = self.__router
        converters = self._defaults.copy()
        default = self._default_case

        for key, converter in converters.items():
            if converter is None:
                router_converter = getattr(router, f'{key}')
                converters[key] = default if router_converter is None else router_converter

        return converters
