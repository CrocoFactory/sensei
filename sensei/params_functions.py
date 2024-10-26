from typing import Any, Callable, List, Optional, Union

from ._internal import (Path as _params_Path, Query as _params_Query, Cookie as _params_Cookie,
                        Header as _params_Header, Body as _params_Body, File as _params_File,
                        Form as _params_Form, Undefined)

_Unset: Any = Undefined


def Path(
        default: Any = ...,
        *,
        default_factory: Union[Callable[[], Any], None] = _Unset,
        alias: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        discriminator: Union[str, None] = None,
        strict: Union[bool, None] = _Unset,
        multiple_of: Union[float, None] = _Unset,
        allow_inf_nan: Union[bool, None] = _Unset,
        max_digits: Union[int, None] = _Unset,
        decimal_places: Union[int, None] = _Unset,
        examples: Optional[List[Any]] = None,
        **extra: Any,
) -> _params_Path:
    """
    Declare a path parameter for a path operation.

    Args:
        default (Any):
            Default value if the parameter field is not set.
        default_factory (Union[Callable[[], Any], None]):
            Callable to generate the default value.
        alias (Optional[str]):
            Alternative name for the parameter field, used for data extraction,
            useful when parameter name conflicts with reserved words.
        title (Optional[str]):
            Human-readable title for the parameter.
        description (Optional[str]):
            Human-readable description for the parameter.
        gt (Optional[float]):
            Specifies that the value must be greater than this value, applicable only to numbers.
        ge (Optional[float]):
            Specifies that the value must be greater than or equal to this value, applicable only to numbers.
        lt (Optional[float]):
            Specifies that the value must be less than this value, applicable only to numbers.
        le (Optional[float]):
            Specifies that the value must be less than or equal to this value, applicable only to numbers.
        min_length (Optional[int]):
            Minimum length for string values.
        max_length (Optional[int]):
            Maximum length for string values.
        pattern (Optional[str]):
            Regular expression pattern for string values.
        discriminator (Union[str, None]):
            Field name for discriminating the type in a tagged union.
        strict (Union[bool, None]):
            Enables strict validation if set to `True`.
        multiple_of (Union[float, None]):
            Specifies that the value must be a multiple of this value, applicable only to numbers.
        allow_inf_nan (Union[bool, None]):
            Allows values `inf`, `-inf`, and `nan`, applicable only to numbers.
        max_digits (Union[int, None]):
            Maximum number of digits allowed for numeric values.
        decimal_places (Union[int, None]):
            Maximum number of decimal places allowed for numeric values.
        examples (Optional[List[Any]]):
            Example values for the parameter.
        **extra (Any):
            Extra fields for JSON Schema. This argument is deprecated in favor of `json_schema_extra`.

    Returns:
        _params_Path: path parameter for a *path operation*.
    """
    return _params_Path(
        default=default,
        default_factory=default_factory,
        alias=alias,
        title=title,
        description=description,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        discriminator=discriminator,
        strict=strict,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        max_digits=max_digits,
        decimal_places=decimal_places,
        example=_Unset,
        examples=examples,
        **extra,
    )


def Query(
        default: Any = Undefined,
        *,
        default_factory: Union[Callable[[], Any], None] = _Unset,
        alias: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        discriminator: Union[str, None] = None,
        strict: Union[bool, None] = _Unset,
        multiple_of: Union[float, None] = _Unset,
        allow_inf_nan: Union[bool, None] = _Unset,
        max_digits: Union[int, None] = _Unset,
        decimal_places: Union[int, None] = _Unset,
        examples: Optional[List[Any]] = None,
        **extra: Any,
) -> _params_Query:
    """
    Declare a query parameter for a path operation.

    Args:
        default (Any):
            Default value if the parameter field is not set.
        default_factory (Union[Callable[[], Any], None]):
            Callable to generate the default value.
        alias (Optional[str]):
            Alternative name for the parameter field, used when parameter name
            conflicts with reserved words.
        title (Optional[str]):
            Human-readable title for the parameter.
        description (Optional[str]):
            Human-readable description for the parameter.
        gt (Optional[float]):
            Specifies that the value must be greater than this value, applicable only to numbers.
        ge (Optional[float]):
            Specifies that the value must be greater than or equal to this value, applicable only to numbers.
        lt (Optional[float]):
            Specifies that the value must be less than this value, applicable only to numbers.
        le (Optional[float]):
            Specifies that the value must be less than or equal to this value, applicable only to numbers.
        min_length (Optional[int]):
            Minimum length for string values.
        max_length (Optional[int]):
            Maximum length for string values.
        pattern (Optional[str]):
            Regular expression pattern for string values.
        discriminator (Union[str, None]):
            Field name for discriminating the type in a tagged union.
        strict (Union[bool, None]):
            Enables strict validation if set to `True`.
        multiple_of (Union[float, None]):
            Specifies that the value must be a multiple of this value, applicable only to numbers.
        allow_inf_nan (Union[bool, None]):
            Allows values `inf`, `-inf`, and `nan`, applicable only to numbers.
        max_digits (Union[int, None]):
            Maximum number of digits allowed for numeric values.
        decimal_places (Union[int, None]):
            Maximum number of decimal places allowed for numeric values.
        examples (Optional[List[Any]]):
            Example values for the parameter.
        **extra (Any):
            Extra fields for JSON Schema.

    Returns:
        _params_Query: query parameter for a *path operation*.
    """
    return _params_Query(
        default=default,
        default_factory=default_factory,
        alias=alias,
        title=title,
        description=description,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        discriminator=discriminator,
        strict=strict,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        max_digits=max_digits,
        decimal_places=decimal_places,
        examples=examples,
        **extra,
    )


def Header(
        default: Any = Undefined,
        *,
        default_factory: Union[Callable[[], Any], None] = _Unset,
        alias: Optional[str] = None,
        convert_underscores: bool = True,
        title: Optional[str] = None,
        description: Optional[str] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        discriminator: Union[str, None] = None,
        strict: Union[bool, None] = _Unset,
        multiple_of: Union[float, None] = _Unset,
        allow_inf_nan: Union[bool, None] = _Unset,
        max_digits: Union[int, None] = _Unset,
        decimal_places: Union[int, None] = _Unset,
        examples: Optional[List[Any]] = None,
        **extra: Any,
) -> _params_Header:
    """
    Declare a header parameter for a path operation.

    Args:
        default (Any):
            Default value if the parameter field is not set.
        default_factory (Union[Callable[[], Any], None]):
            Callable to generate the default value.
        alias (Optional[str]):
            Alternative name for the parameter field, used when parameter name
            conflicts with reserved words.
        convert_underscores (bool):
            Automatically converts underscores to hyphens in the parameter name.
        title (Optional[str]):
            Human-readable title for the parameter.
        description (Optional[str]):
            Human-readable description for the parameter.
        gt (Optional[float]):
            Specifies that the value must be greater than this value, applicable only to numbers.
        ge (Optional[float]):
            Specifies that the value must be greater than or equal to this value, applicable only to numbers.
        lt (Optional[float]):
            Specifies that the value must be less than this value, applicable only to numbers.
        le (Optional[float]):
            Specifies that the value must be less than or equal to this value, applicable only to numbers.
        min_length (Optional[int]):
            Minimum length for string values.
        max_length (Optional[int]):
            Maximum length for string values.
        pattern (Optional[str]):
            Regular expression pattern for string values.
        discriminator (Union[str, None]):
            Field name for discriminating the type in a tagged union.
        strict (Union[bool, None]):
            Enables strict validation if set to `True`.
        multiple_of (Union[float, None]):
            Specifies that the value must be a multiple of this value, applicable only to numbers.
        allow_inf_nan (Union[bool, None]):
            Allows values `inf`, `-inf`, and `nan`, applicable only to numbers.
        max_digits (Union[int, None]):
            Maximum number of digits allowed for numeric values.
        decimal_places (Union[int, None]):
            Maximum number of decimal places allowed for numeric values.
        examples (Optional[List[Any]]):
            Example values for the parameter.
        **extra (Any):
            Extra fields for JSON Schema.

    Returns:
        _params_Header: header parameter for a *path operation*.
    """
    return _params_Header(
        default=default,
        default_factory=default_factory,
        alias=alias,
        title=title,
        description=description,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        discriminator=discriminator,
        strict=strict,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        max_digits=max_digits,
        decimal_places=decimal_places,
        examples=examples,
        **extra,
    )


def Cookie(
        default: Any = Undefined,
        *,
        default_factory: Union[Callable[[], Any], None] = _Unset,
        alias: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        discriminator: Union[str, None] = None,
        strict: Union[bool, None] = _Unset,
        multiple_of: Union[float, None] = _Unset,
        allow_inf_nan: Union[bool, None] = _Unset,
        max_digits: Union[int, None] = _Unset,
        decimal_places: Union[int, None] = _Unset,
        examples: Optional[List[Any]] = None,
        **extra: Any,
) -> _params_Cookie:
    """
    Declare a cookie parameter for a path operation.

    Args:
        default (Any):
            Default value if the parameter field is not set.
        default_factory (Union[Callable[[], Any], None]):
            Callable to generate the default value.
        alias (Optional[str]):
            Alternative name for the parameter field, used when parameter name
            conflicts with reserved words.
        title (Optional[str]):
            Human-readable title for the parameter.
        description (Optional[str]):
            Human-readable description for the parameter.
        gt (Optional[float]):
            Specifies that the value must be greater than this value, applicable only to numbers.
        ge (Optional[float]):
            Specifies that the value must be greater than or equal to this value, applicable only to numbers.
        lt (Optional[float]):
            Specifies that the value must be less than this value, applicable only to numbers.
        le (Optional[float]):
            Specifies that the value must be less than or equal to this value, applicable only to numbers.
        min_length (Optional[int]):
            Minimum length for string values.
        max_length (Optional[int]):
            Maximum length for string values.
        pattern (Optional[str]):
            Regular expression pattern for string values.
        discriminator (Union[str, None]):
            Field name for discriminating the type in a tagged union.
        strict (Union[bool, None]):
            Enables strict validation if set to `True`.
        multiple_of (Union[float, None]):
            Specifies that the value must be a multiple of this value, applicable only to numbers.
        allow_inf_nan (Union[bool, None]):
            Allows values `inf`, `-inf`, and `nan`, applicable only to numbers.
        max_digits (Union[int, None]):
            Maximum number of digits allowed for numeric values.
        decimal_places (Union[int, None]):
            Maximum number of decimal places allowed for numeric values.
        examples (Optional[List[Any]]):
            Example values for the parameter.
        **extra (Any):
            Extra fields for JSON Schema.

    Returns:
        _params_Cookie: cookie parameter for a *path operation*.
    """
    return _params_Cookie(
        default=default,
        default_factory=default_factory,
        alias=alias,
        title=title,
        description=description,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        discriminator=discriminator,
        strict=strict,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        max_digits=max_digits,
        decimal_places=decimal_places,
        examples=examples,
        **extra,
    )


def Body(
        default: Any = Undefined,
        *,
        default_factory: Union[Callable[[], Any], None] = _Unset,
        embed: bool = True,
        media_type: str = "application/json",
        alias: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        discriminator: Union[str, None] = None,
        strict: Union[bool, None] = _Unset,
        multiple_of: Union[float, None] = _Unset,
        allow_inf_nan: Union[bool, None] = _Unset,
        max_digits: Union[int, None] = _Unset,
        decimal_places: Union[int, None] = _Unset,
        examples: Optional[List[Any]] = None,
        **extra: Any,
) -> _params_Body:
    """
    Declare a body parameter for a path operation.

    Args:
        default (Any):
            Default value if the parameter field is not set.
        default_factory (Union[Callable[[], Any], None]):
            Callable to generate the default value.
        embed (bool):
            If `True`, the parameter will be expected in a JSON body as a key, instead
            of being the JSON body itself.
        media_type (str):
            The media type of this parameter field, e.g., "application/json".
        alias (Optional[str]):
            Alternative name for the parameter field, used when parameter name
            conflicts with reserved words.
        title (Optional[str]):
            Human-readable title for the parameter.
        description (Optional[str]):
            Human-readable description for the parameter.
        gt (Optional[float]):
            Specifies that the value must be greater than this value, applicable only to numbers.
        ge (Optional[float]):
            Specifies that the value must be greater than or equal to this value, applicable only to numbers.
        lt (Optional[float]):
            Specifies that the value must be less than this value, applicable only to numbers.
        le (Optional[float]):
            Specifies that the value must be less than or equal to this value, applicable only to numbers.
        min_length (Optional[int]):
            Minimum length for string values.
        max_length (Optional[int]):
            Maximum length for string values.
        pattern (Optional[str]):
            Regular expression pattern for string values.
        discriminator (Union[str, None]):
            Field name for discriminating the type in a tagged union.
        strict (Union[bool, None]):
            Enables strict validation if set to `True`.
        multiple_of (Union[float, None]):
            Specifies that the value must be a multiple of this value, applicable only to numbers.
        allow_inf_nan (Union[bool, None]):
            Allows values `inf`, `-inf`, and `nan`, applicable only to numbers.
        max_digits (Union[int, None]):
            Maximum number of digits allowed for numeric values.
        decimal_places (Union[int, None]):
            Maximum number of decimal places allowed for numeric values.
        examples (Optional[List[Any]]):
            Example values for the parameter.
        **extra (Any):
            Extra fields for JSON Schema.

    Returns:
        _params_Body: body parameter for a *path operation*.
    """
    return _params_Body(
        default=default,
        default_factory=default_factory,
        embed=embed,
        media_type=media_type,
        alias=alias,
        title=title,
        description=description,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        discriminator=discriminator,
        strict=strict,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        max_digits=max_digits,
        decimal_places=decimal_places,
        examples=examples,
        **extra,
    )


def Form(
        default: Any = Undefined,
        *,
        default_factory: Union[Callable[[], Any], None] = _Unset,
        embed: bool = True,
        alias: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        discriminator: Union[str, None] = None,
        strict: Union[bool, None] = _Unset,
        multiple_of: Union[float, None] = _Unset,
        allow_inf_nan: Union[bool, None] = _Unset,
        max_digits: Union[int, None] = _Unset,
        decimal_places: Union[int, None] = _Unset,
        examples: Optional[List[Any]] = None,
        **extra: Any,
) -> Any:
    """
    Declare a form parameter for a path operation.

    Args:
        default (Any):
            Default value if the parameter field is not set.
        default_factory (Union[Callable[[], Any], None]):
            Callable to generate the default value.
        embed (bool):
            If `True`, the parameter will be expected in a JSON body as a key, instead
            of being the JSON body itself.
        alias (Optional[str]):
            Alternative name for the parameter field, used when parameter name
            conflicts with reserved words.
        title (Optional[str]):
            Human-readable title for the parameter.
        description (Optional[str]):
            Human-readable description for the parameter.
        gt (Optional[float]):
            Specifies that the value must be greater than this value, applicable only to numbers.
        ge (Optional[float]):
            Specifies that the value must be greater than or equal to this value, applicable only to numbers.
        lt (Optional[float]):
            Specifies that the value must be less than this value, applicable only to numbers.
        le (Optional[float]):
            Specifies that the value must be less than or equal to this value, applicable only to numbers.
        min_length (Optional[int]):
            Minimum length for string values.
        max_length (Optional[int]):
            Maximum length for string values.
        pattern (Optional[str]):
            Regular expression pattern for string values.
        discriminator (Union[str, None]):
            Field name for discriminating the type in a tagged union.
        strict (Union[bool, None]):
            Enables strict validation if set to `True`.
        multiple_of (Union[float, None]):
            Specifies that the value must be a multiple of this value, applicable only to numbers.
        allow_inf_nan (Union[bool, None]):
            Allows values `inf`, `-inf`, and `nan`, applicable only to numbers.
        max_digits (Union[int, None]):
            Maximum number of digits allowed for numeric values.
        decimal_places (Union[int, None]):
            Maximum number of decimal places allowed for numeric values.
        examples (Optional[List[Any]]):
            Example values for the parameter.
        **extra (Any):
            Extra fields for JSON Schema.

    Returns:
        Any: form parameter for a *path operation*.
    """
    media_type = "application/x-www-form-urlencoded"
    return _params_Form(
        default=default,
        default_factory=default_factory,
        embed=embed,
        media_type=media_type,
        alias=alias,
        title=title,
        description=description,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        discriminator=discriminator,
        strict=strict,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        max_digits=max_digits,
        decimal_places=decimal_places,
        examples=examples,
        **extra,
    )

def File(
        default: Any = Undefined,
        *,
        default_factory: Union[Callable[[], Any], None] = _Unset,
        alias: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        gt: Optional[float] = None,
        ge: Optional[float] = None,
        lt: Optional[float] = None,
        le: Optional[float] = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        discriminator: Union[str, None] = None,
        strict: Union[bool, None] = _Unset,
        multiple_of: Union[float, None] = _Unset,
        allow_inf_nan: Union[bool, None] = _Unset,
        max_digits: Union[int, None] = _Unset,
        decimal_places: Union[int, None] = _Unset,
        examples: Optional[List[Any]] = None,
        **extra: Any,
) -> Any:
    """
    Declare a file parameter for a path operation.

    Args:
        default (Any):
            Default value if the parameter field is not set.
        default_factory (Union[Callable[[], Any], None]):
            Callable to generate the default value.
        alias (Optional[str]):
            Alternative name for the parameter field, used when parameter name
            conflicts with reserved words.
        title (Optional[str]):
            Human-readable title for the parameter.
        description (Optional[str]):
            Human-readable description for the parameter.
        gt (Optional[float]):
            Specifies that the value must be greater than this value, applicable only to numbers.
        ge (Optional[float]):
            Specifies that the value must be greater than or equal to this value, applicable only to numbers.
        lt (Optional[float]):
            Specifies that the value must be less than this value, applicable only to numbers.
        le (Optional[float]):
            Specifies that the value must be less than or equal to this value, applicable only to numbers.
        min_length (Optional[int]):
            Minimum length for string values.
        max_length (Optional[int]):
            Maximum length for string values.
        pattern (Optional[str]):
            Regular expression pattern for string values.
        discriminator (Union[str, None]):
            Field name for discriminating the type in a tagged union.
        strict (Union[bool, None]):
            Enables strict validation if set to `True`.
        multiple_of (Union[float, None]):
            Specifies that the value must be a multiple of this value, applicable only to numbers.
        allow_inf_nan (Union[bool, None]):
            Allows values `inf`, `-inf`, and `nan`, applicable only to numbers.
        max_digits (Union[int, None]):
            Maximum number of digits allowed for numeric values.
        decimal_places (Union[int, None]):
            Maximum number of decimal places allowed for numeric values.
        examples (Optional[List[Any]]):
            Example values for the parameter.
        **extra (Any):
            Extra fields for JSON Schema.

    Returns:
        Any: file parameter for a *path operation*.
    """
    media_type = "multipart/form-data"
    return _params_File(
        default=default,
        default_factory=default_factory,
        media_type=media_type,
        alias=alias,
        title=title,
        description=description,
        gt=gt,
        ge=ge,
        lt=lt,
        le=le,
        min_length=min_length,
        max_length=max_length,
        pattern=pattern,
        discriminator=discriminator,
        strict=strict,
        multiple_of=multiple_of,
        allow_inf_nan=allow_inf_nan,
        max_digits=max_digits,
        decimal_places=decimal_places,
        examples=examples,
        **extra,
    )
