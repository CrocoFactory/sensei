from typing import Literal, Self
from enum import StrEnum

HTTPMethod = Literal[
    "GET",
    "POST",
    "PUT",
    "DELETE",
    "PATCH",
    "HEAD",
    "OPTIONS",
    "CONNECT",
    "TRACE"
]


class MethodType(StrEnum):
    INSTANCE = "instance"
    CLASS = "class"
    STATIC = "static"

    @classmethod
    def self_method(cls, method: Self) -> bool:
        return method in (cls.CLASS, cls.INSTANCE)
