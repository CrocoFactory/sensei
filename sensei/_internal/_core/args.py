from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from sensei.types import Json


class Args(BaseModel):
    """
    Model used in preparers as input and output argument. Stores request arguments

    Attributes:
        url (str): URL to which the request will be made.
        params (dict[str, Any]): Dictionary of query parameters to be included in the URL.
        data (dict[str, Any]): Dictionary of payload for the request body.
        json_ (Json): JSON payload for the request body.
                                The field is aliased as 'json' and defaults to an empty dictionary.
        files (dict[str, Any]): File payload for the request body.
        headers (dict[str, Any]): Dictionary of HTTP headers to be sent with the request.
        cookies (dict[str, Any]): Dictionary of cookies to be included in the request.
    """

    model_config = ConfigDict(validate_assignment=True)

    url: str
    params: dict[str, Any] = {}
    json_: Json = Field({}, alias="json")
    data: Any = {}
    headers: dict[str, Any] = {}
    cookies: dict[str, Any] = {}
    files: dict[str, Any] = {}

    def model_dump(self, *args, **kwargs) -> dict[str, Any]:
        data = super().model_dump(*args, exclude={'files'}, **kwargs)
        data['files'] = self.files
        return self._exclude_none(data)

    @classmethod
    def _exclude_none(cls, data: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(data, dict):
            return data
        return {k: cls._exclude_none(v) for k, v in data.items() if v is not None}
