import json
import os
import time
from abc import ABC, abstractmethod
from enum import Enum
from http import HTTPStatus as Status
from typing import Callable
from urllib.parse import parse_qs

import jwt
import requests
from httpx import Response, Request
from pydantic import BaseModel
from respx import MockRouter

Responser = Callable[[Request], Response]
SECRET_TOKEN = os.urandom(32).hex()
JWT_ALGORITHM = 'HS256'


def get_jwt_token(email: str) -> str:
    payload = {
        'sub': email,
        'exp': time.time() + 10 * 60
    }
    token = jwt.encode(payload, SECRET_TOKEN, algorithm=JWT_ALGORITHM)
    return token


def form_to_json(form_str: str) -> dict:
    parsed_dict = {k: v[0] for k, v in parse_qs(form_str).items()}
    return parsed_dict


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
        token = get_jwt_token(email)
        return Response(status_code=Status.CREATED.value, json={'data': {'token': token}})

    @staticmethod
    def method() -> str:
        return "POST"

    @staticmethod
    def path() -> str:
        return "/token"


class UploadImage(_Endpoint):
    @staticmethod
    def responser(request: Request) -> Response:
        image = request.content
        res = requests.post('"https://httpbin.org/post"', )

        if not image:
            return Response(status_code=Status.BAD_REQUEST)
        return Response(status_code=Status.CREATED, json={'icon': str(image)[2:-1]})

    @staticmethod
    def method() -> str:
        return "POST"

    @staticmethod
    def path() -> str:
        return "/upload_image"


class Register(_Endpoint):
    @staticmethod
    def responser(request: Request) -> Response:
        user = form_to_json(request.content.decode())

        token = get_jwt_token(user['email'])
        return Response(status_code=Status.CREATED, json={'token': token})

    @staticmethod
    def method() -> str:
        return "POST"

    @staticmethod
    def path() -> str:
        return "/register"


def mock_api(router: MockRouter, base_url: str, path: str) -> None:
    api = _Endpoint.endpoints

    for endpoint in api:
        if path == endpoint.path:
            url = base_url + endpoint.path
            router.request(method=endpoint.method, url=url).mock(side_effect=endpoint.responser)
            break
    else:
        raise ValueError('Path not found')
