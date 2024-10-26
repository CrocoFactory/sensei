from __future__ import annotations

from functools import partial
from typing import Any, get_args, Callable, Generic, get_origin

from pydantic import BaseModel, ConfigDict

from sensei._utils import format_str
from sensei.types import IResponse
from ._case_converters import CaseConverters
from ._params_parser import ParamsParser
from ._types import ResponseModel, Args
from ..tools import split_params, make_model, HTTPMethod, validate_method

_ConditionChecker = Callable[[type[ResponseModel]], bool]
_ResponseHandler = Callable[[type[ResponseModel], IResponse], ResponseModel]
_PartialHandler = Callable[[IResponse], ResponseModel]


class Endpoint(Generic[ResponseModel]):
    __slots__ = (
        "_path",
        "_method",
        "_parser",
        "_params_model",
        "_response_model",
    )

    _response_handle_map: dict[_ConditionChecker, _ResponseHandler] = {
        lambda model: isinstance(model, type(BaseModel)): lambda model, response: model(**response.json()),
        lambda model: model is str: lambda model, response: response.text,
        lambda model: dict in (model, get_origin(model)): lambda model, response: (
            response.json() if response.request.method not in('HEAD', 'OPTIONS') else dict(list(response.headers.items()))),
        lambda model: model is bytes: lambda model, response: response.content,
        lambda model: isinstance(model, BaseModel): lambda model, response: model,
        lambda model: model is None: lambda model, response: None,
        lambda model: get_origin(model) is list and len(get_args(model)) == 1 and isinstance(get_args(model)[0], type(BaseModel)):
            lambda model, response: [get_args(model)[0](**value) for value in response.json()],
        lambda model: (get_origin(model) is list and len(get_args(model)) == 1
                       and ((arg := get_args(model)[0]) is dict or get_origin(arg) is dict)):
            lambda model, response: response.json(),
    }

    def __init__(
            self,
            path: str,
            method: HTTPMethod,
            /, *,
            params: dict[str, Any] | None = None,
            response: type[ResponseModel] | None = None,
            case_converters: CaseConverters
    ):
        validate_method(method)

        self._path = path
        self._method = method

        params_model = self._make_model('Params', params)

        self._params_model = params_model
        self._response_model = response
        self._parser = ParamsParser(method, case_converters)

    @property
    def path(self) -> str:
        return self._path

    @property
    def method(self) -> HTTPMethod:
        return self._method

    @property
    def params_model(self) -> type[BaseModel] | None:
        return self._params_model

    @property
    def response_model(self) -> type[ResponseModel] | None:
        return self._response_model

    @staticmethod
    def _make_model(
            model_name: str,
            model_args: dict[str, Any] | None,
            model_config: ConfigDict | None = None,
    ) -> type[BaseModel] | None:
        if model_args:
            return make_model(model_name, model_args, model_config)
        else:
            return None

    @classmethod
    def _handle_if_condition(cls, model: type[ResponseModel]) -> _PartialHandler:
        for checker, handler in cls._response_handle_map.items():
            if checker(model):
                result = partial(handler, model)
                break
        else:
            raise ValueError(f'Unsupported response type {model}')

        return result

    @classmethod
    def is_response_type(cls, value: Any) -> bool:
        try:
            cls._handle_if_condition(value)
            return True
        except ValueError:
            return False

    def validate_response(self, response: Any) -> None:
        response_model = self.response_model

        if isinstance(response_model, BaseModel):
            response_model = type(response_model)

        class ValidationModel(BaseModel):
            model_config = ConfigDict(arbitrary_types_allowed=True)
            result: response_model

        ValidationModel(result=response)

    def get_args(self, **kwargs) -> Args:
        params_model = self.params_model
        path = self.path
        if params_model:
            url, request_params = self._get_init_args(params_model, **kwargs)
        else:
            url = path
            request_params = {}

        return Args(
            url=url,
            **request_params
        )

    def get_response(self, *, response_obj: IResponse) -> ResponseModel | None:
        response_model = self.response_model

        result = self._handle_if_condition(response_model)(response_obj)

        to_validate = result

        if isinstance(response_model, BaseModel):
            response_model = type(response_model)
            to_validate = response_model(**result.model_dump(mode='json', by_alias=True))

        class ValidationModel(BaseModel):
            result: response_model

        ValidationModel(result=to_validate)

        return result

    def _get_init_args(
            self,
            params_model: type[BaseModel],
            **kwargs
    ) -> tuple[str, dict[str, Any]]:
        path = self.path
        params_model_instance = params_model(**kwargs)
        params_all = params_model_instance.model_dump(mode='python', by_alias=True)
        params, path_params = split_params(path, params_all)

        fields = params_model.model_fields.copy()
        fields, _ = split_params(path, fields)

        request_params = self._parser(fields, params)

        url = format_str(path, path_params, True)
        return url, request_params
