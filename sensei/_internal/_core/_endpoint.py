from __future__ import annotations

from functools import partial
from pydantic import BaseModel, Field
from sensei.types import IResponse, Json
from sensei._utils import format_str
from sensei._params import Body, Query, Header, Cookie, Param
from sensei.cases import header_case as to_header_case
from typing import Any, get_args, Callable, TypeVar, Generic, get_origin
from ..tools import ChainedMap, split_params, make_model, is_safe_method, HTTPMethod, validate_method, identical

CaseConverter = Callable[[str], str]

ResponseModel = TypeVar(
    'ResponseModel',
    type[BaseModel],
    str,
    dict,
    bytes,
    list[dict],
    BaseModel,
    list[BaseModel],
)

RESPONSE_TYPES = ResponseModel.__constraints__
_ConditionChecker = Callable[[type[ResponseModel]], bool]
_ResponseHandler = Callable[[type[ResponseModel], IResponse], ResponseModel]
_PartialHandler = Callable[[IResponse], ResponseModel]


class Args(BaseModel):
    """
    Model used in preparers as input and output argument. Stores request arguments

    Attributes:
        url (str): URL to which the request will be made.
        params (dict[str, Any]): Dictionary of query parameters to be included in the URL.
                                 Default is an empty dictionary.
        json_ (Json): JSON payload for the request body.
                                The field is aliased as 'json' and defaults to an empty dictionary.
        headers (dict[str, Any]): Dictionary of HTTP headers to be sent with the request.
                                  Default is an empty dictionary.
        cookies (dict[str, Any]): Dictionary of cookies to be included in the request.
                                  Default is an empty dictionary.
    """
    url: str
    params: dict[str, Any] = {}
    json_: Json = Field({}, alias="json")
    headers: dict[str, Any] = {}
    cookies: dict[str, Any] = {}


class Endpoint(Generic[ResponseModel]):
    __slots__ = (
        "_path",
        "_method",
        "_error_msg",
        "_case_converters",
        "_params_model",
        "_response_model",
    )

    _response_handle_map: dict[_ConditionChecker, _ResponseHandler] = {
        lambda model: isinstance(model, type(BaseModel)): lambda model, response: model(**response.json()),
        lambda model: model is str: lambda model, response: response.text,
        lambda model: dict in (model, get_origin(model)): lambda model, response: response.json(),
        lambda model: model is bytes: lambda model, response: response.content,
        lambda model: isinstance(model, BaseModel): lambda model, response: model,
        lambda model: model is None: lambda model, response: None,
        lambda model: get_origin(model) is list and isinstance(get_args(model)[0], type(BaseModel)):
            lambda model, response: [get_args(model)[0](**value) for value in response.json()],
        lambda model: (get_origin(model) is list and ((arg := get_args(model)[0]) is dict or get_origin(arg) is dict)):
            lambda model, response: response.json(),
    }

    def __init__(
            self,
            path: str,
            method: HTTPMethod,
            /, *,
            params: dict[str, Any] | None = None,
            response: type[ResponseModel] | None = None,
            error_msg: str | None = None,
            query_case: CaseConverter | None = None,
            body_case: CaseConverter | None = None,
            cookie_case: CaseConverter | None = None,
            header_case: CaseConverter | None = to_header_case
    ):
        validate_method(method)

        self._path = path
        self._method = method
        self._error_msg = error_msg

        params_model = self._make_model('Params', params)

        converters = {
            'params': query_case,
            'json': body_case,
            'cookies': cookie_case,
            'headers': header_case
        }

        for k in converters.keys():
            if converters[k] is None:
                converters[k] = identical

        self._case_converters = converters

        self._params_model = params_model
        self._response_model = response

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
    def _make_model(model_name: str, model_args: dict[str, Any] | None) -> type[BaseModel] | None:
        if model_args:
            return make_model(model_name, model_args)
        else:
            return None

    @classmethod
    def _handle_if_condition(cls, model: type[ResponseModel]) -> _PartialHandler:
        for checker, handler in cls._response_handle_map.items():
            if checker(model):
                result = partial(handler, model)
                break
        else:
            raise ValueError('Unsupported response type')

        return result

    @classmethod
    def is_response_type(cls, value: Any) -> bool:
        try:
            cls._handle_if_condition(value)
            return True
        except ValueError:
            return False

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
        params_all = params_model_instance.model_dump(mode='json', by_alias=True)
        params, path_params = split_params(path, params_all)

        fields = params_model.model_fields.copy()
        fields, _ = split_params(path, fields)

        request_params = self._map_params(fields, params)

        url = format_str(path, path_params, True)
        return url, request_params

    def _map_params(
            self,
            fields: dict[str, Any],
            params: dict[str, Any]
    ) -> dict[str, Any]:
        new_params = {
            'params': {},
            'json': {},
            'headers': {},
            'cookies': {}
        }

        annotation_map = {
            Query: 'params',
            Body: 'json',
            Cookie: 'cookies',
            Header: 'headers',
        }

        type_to_converter = ChainedMap[type[Param], CaseConverter](annotation_map, self._case_converters)
        type_to_params = ChainedMap[type[Param], dict[str, Any]](annotation_map, new_params)

        for key, value in fields.items():
            types = Body, Cookie, Header, Query
            if isinstance(value, types):
                param_type = type(value)

                converted = type_to_converter[param_type](key)

                alias = value.alias
                result_key = alias if alias else converted
                type_to_params[param_type][result_key] = params[key]
            else:
                param_type = Query if is_safe_method(self.method) else Body

                converted = type_to_converter[param_type](key)
                type_to_params[param_type][converted] = params[key]

        new_params = {k: v for k, v in new_params.items() if v}
        return new_params
