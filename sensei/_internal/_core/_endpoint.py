from __future__ import annotations

from functools import partial
from typing import Any
from typing import TypedDict
from typing import get_args, Callable, Generic, get_origin, TypeVar

from pydantic import BaseModel, ConfigDict
from pydantic.fields import FieldInfo

from sensei._utils import format_str
from sensei.types import IResponse
from ._params import Query, Body, Form, File, Cookie, Header, Param
from .args import Args
from ..tools import ChainedMap, accept_body, HTTPMethod
from ..tools import split_params, make_model, validate_method

_CaseConverter = Callable[[str], str]
_CaseConverters = dict[str, _CaseConverter]


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

_ConditionChecker = Callable[[type[ResponseModel]], bool]
_ResponseHandler = Callable[[type[ResponseModel], IResponse], ResponseModel]
_PartialHandler = Callable[[IResponse], ResponseModel]

RESPONSE_TYPES = ResponseModel.__constraints__


class _RequestParams(TypedDict, total=False):
    params: dict[str, Any]
    json: dict[str, Any]
    headers: dict[str, Any]
    cookies: dict[str, Any]
    data: dict[str, Any]
    files: dict[str, Any]


class ParamsParser:
    def __init__(self, method: HTTPMethod, case_converters: _CaseConverters):
        self._method = method
        self._case_converters = case_converters

    def __call__(
            self,
            fields: dict[str, FieldInfo],
            params: dict[str, Any]
    ) -> _RequestParams:
        new_params = {
            'params': {},
            'json': {},
            'headers': {},
            'cookies': {},
            'data': {},
            'files': {}
        }

        annotation_to_label = {
            Query: 'params',
            Body: 'json',
            Form: 'data',
            File: 'files',
            Cookie: 'cookies',
            Header: 'headers',
        }

        label_to_converter = {
            'params': 'query_case',
            'json': 'body_case',
            'data': 'body_case',
            'files': 'body_case',
            'cookies': 'cookie_case',
            'headers': 'header_case',
        }

        type_to_converter = ChainedMap[type[Param], _CaseConverter](
            annotation_to_label,
            label_to_converter,
            self._case_converters
        )
        type_to_params = ChainedMap[type[Param], dict[str, Any]](annotation_to_label, new_params)

        has_body = False
        has_file_body = False
        has_not_embed = False
        has_embed = False

        media_type = None

        for key, value in fields.items():
            types = Body, Cookie, Header, Query, File, Form
            if isinstance(value, types):
                condition = isinstance(value, Body)
                new_params_key = 'data'
                if condition:
                    multipart = 'multipart/form-data'
                    form_content = ('multipart/form-data', 'application/x-www-form-urlencoded')

                    not_equal = media_type != value.media_type
                    not_multipart = multipart not in (media_type, value.media_type)
                    not_form = value.media_type not in form_content or media_type not in form_content

                    if media_type is not None and (not_equal and (not_multipart or not_form)):
                        raise ValueError(f'Body parameters cannot have different media types. You try to use '
                                         f'{value.media_type} and {media_type}')

                    media_type = value.media_type

                    media_type_map = {
                        'application/json': 'json',
                        'application/vnd.api+json': 'json',
                        'application/ld+json': 'json',
                        'multipart/form-data': ('files', 'data'),
                        'application/x-www-form-urlencoded': 'data'
                    }

                    if result := media_type_map.get(value.media_type):
                        new_params_key = result

                        if isinstance(result, tuple):
                            if isinstance(value, File):
                                new_params_key = result[0]
                            else:
                                new_params_key = result[1]
                    else:
                        new_params_key = 'data'
                        new_params['headers']['Content-Type'] = value.media_type

                param_type = type(value)

                converter = type_to_converter[param_type]
                converted = converter(key)

                alias = value.alias
                result_key = alias if alias else converted

                if condition:
                    if not value.embed:
                        if has_embed:
                            raise ValueError('Embed and non-embed variants of body are provided.')

                        if value.media_type == 'multipart/form-data':
                            if isinstance(value, File):
                                if has_file_body:
                                    raise ValueError('Multiple variants of non-embed file body are provided.')
                                has_file_body = True
                            else:
                                has_body = True

                        if has_body:
                            raise ValueError('Multiple variants of non-embed body are provided.')
                        else:
                            has_body = True

                        has_not_embed = True
                        new_params[new_params_key] = params[key]
                    else:
                        if has_not_embed:
                            raise ValueError('Embed and non-embed variants of body are provided.')
                        has_embed = True
                        new_params[new_params_key][result_key] = params[key]
                else:
                    type_to_params[param_type][result_key] = params[key]
            else:
                param_type = Body if accept_body(self._method) else Query

                converted = type_to_converter[param_type](key)
                type_to_params[param_type][converted] = params[key]

        new_params = {k: v for k, v in new_params.items() if v}
        return new_params


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
            response.json() if response.request.method not in ('HEAD', 'OPTIONS') else dict(
                list(response.headers.items()))
        ),
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
            case_converters: _CaseConverters
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
