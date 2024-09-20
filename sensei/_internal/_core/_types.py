from abc import ABC, abstractmethod
from typing import Protocol, TypeVar, Any
from ._endpoint import CaseConverter
from ._requester import Finalizer, Initializer
from ..tools import MethodType


class RoutedFunction(Protocol):
    def __call__(self, *args, **kwargs):
        ...

    def initializer(self, initializer: Initializer) -> Initializer:
        ...

    def finalizer(self, finalizer: Finalizer) -> Finalizer:
        ...

    __method_type__: MethodType
    __name__: str
    __doc__: str


class RoutedMethod(Protocol):
    __func__: RoutedFunction
    __name__: str
    __doc__: str


class RoutedModel(Protocol):
    __router__ = ...

    def __process_json__(self, value: dict[str, Any]) -> dict[str, Any]:
        pass


SameModel = TypeVar("SameModel", bound=RoutedModel)


class IRouter(ABC):
    @abstractmethod
    def model(self, model_obj: SameModel) -> SameModel:
        pass

    @abstractmethod
    def get(
            self,
            path: str,
            /, *,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None
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
            header_case: CaseConverter | None = None
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
            header_case: CaseConverter | None = None
    ) -> RoutedFunction:
        pass

    @abstractmethod
    def delete(
            self,
            path: str,
            /, *,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = None
    ) -> RoutedFunction:
        pass
