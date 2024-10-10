from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, TypeVar
from ._endpoint import CaseConverter
from ._requester import ResponseFinalizer, Preparer, JsonFinalizer
from ..tools import MethodType
from sensei.client import Manager
from sensei.types import IRateLimit


class RoutedFunction(Protocol):
    def __call__(self, *args, **kwargs):
        ...

    def prepare(self, preparer: Preparer | None = None) -> Preparer:
        ...

    def finalize(self, finalizer: ResponseFinalizer | None = None) -> ResponseFinalizer:
        ...

    __method_type__: MethodType
    __name__: str
    __doc__: str


class RoutedMethod(Protocol):
    __func__: RoutedFunction
    __name__: str
    __doc__: str


class _RoutedModel(Protocol):
    __router__ = ...
    __finalize_json__: JsonFinalizer
    __prepare_args__: Preparer
    __query_case__: CaseConverter
    __body_case__: CaseConverter
    __cookie_case__: CaseConverter
    __header_case__: CaseConverter


RoutedModel = TypeVar("RoutedModel", bound=_RoutedModel)


class IRouter(ABC):
    __slots__ = ()

    @property
    @abstractmethod
    def manager(self) -> Manager:
        pass

    @property
    @abstractmethod
    def port(self) -> int:
        pass

    @property
    @abstractmethod
    def rate_limit(self) -> IRateLimit:
        pass

    @abstractmethod
    def model(self, model_obj: RoutedModel | None) -> RoutedModel:
        pass

    @abstractmethod
    def get(
            self,
            path: str,
            /, *,
            query_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
    ) -> RoutedFunction:
        pass

    @abstractmethod
    def post(
            self,
            path: str,
            /, *,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
    ) -> RoutedFunction:
        pass

    @abstractmethod
    def patch(
            self,
            path: str,
            /, *,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
    ) -> RoutedFunction:
        pass

    @abstractmethod
    def put(
            self,
            path: str,
            /, *,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
    ) -> RoutedFunction:
        pass

    @abstractmethod
    def delete(
            self,
            path: str,
            /, *,
            query_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
    ) -> RoutedFunction:
        pass

    @abstractmethod
    def options(
            self,
            path: str,
            /, *,
            query_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
    ) -> RoutedFunction:
        pass

    @abstractmethod
    def head(
            self,
            path: str,
            /, *,
            query_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None,
            skip_finalizer: bool = False,
    ) -> RoutedFunction:
        pass
