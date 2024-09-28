import json
import os
import time
import jwt
from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable
from httpx import Response, Request
from respx import MockRouter
from pydantic import BaseModel
from http import HTTPStatus as Status

Responser = Callable[[Request], Response]
SECRET_TOKEN = os.urandom(32).hex()
JWT_ALGORITHM = 'HS256'


class _HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD",
    OPTIONS = "OPTIONS"
    CONNECT = "CONNECT"
    TRACE = "TRACE"

    def __str__(self) -> str:
        return self.value


class Endpoint(BaseModel):
    responser: Responser
    method: _HTTPMethod
    path: str


class _Endpoint(ABC):
    endpoints: list[Endpoint] = []

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        _Endpoint.endpoints.append(Endpoint(
            responser=cls.responser,
            method=cls.method(),  # type: ignore
            path=cls.path()  # type: ignore
        ))

    @staticmethod
    @abstractmethod
    def responser(request: Request) -> Response:
        pass

    @staticmethod
    @abstractmethod
    def method() -> str:
        pass

    @staticmethod
    @abstractmethod
    def path() -> str:
        pass


class Token(_Endpoint):
    @staticmethod
    def responser(request: Request) -> Response:
        json_ = json.loads(request.content.decode())
        email = json_['email']
        payload = {
            'sub': email,
            'exp': time.time() + 10 * 60
        }
        token = jwt.encode(payload, SECRET_TOKEN, algorithm=JWT_ALGORITHM)
        return Response(status_code=Status.CREATED.value, json={'data': {'token': token}})

    @staticmethod
    def method() -> str:
        return "POST"

    @staticmethod
    def path() -> str:
        return "/token"


def mock_api(router: MockRouter, base_url: str) -> None:
    api = _Endpoint.endpoints

    for endpoint in api:
        url = base_url + endpoint.path
        router.request(method=endpoint.method, url=url).mock(side_effect=endpoint.responser)
