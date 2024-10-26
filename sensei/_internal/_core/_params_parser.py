from typing import Any
from typing import TypedDict

from pydantic.fields import FieldInfo

from ._case_converters import CaseConverters, CaseConverter
from ._params import Query, Body, Form, File, Cookie, Header, Param
from ..tools import ChainedMap, accept_body, HTTPMethod


class _RequestParams(TypedDict, total=False):
    params: dict[str, Any]
    json: dict[str, Any]
    headers: dict[str, Any]
    cookies: dict[str, Any]
    data: dict[str, Any]
    files: dict[str, Any]


class ParamsParser:
    def __init__(self, method: HTTPMethod, case_converters: CaseConverters):
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

        type_to_converter = ChainedMap[type[Param], CaseConverter](
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
