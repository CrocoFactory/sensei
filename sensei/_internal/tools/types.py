from typing import Literal
from enum import Enum
from typing_extensions import Self

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


class MethodType(Enum):
    INSTANCE = "instance"
    CLASS = "class"
    STATIC = "static"

    @classmethod
    def self_method(cls, method: Self) -> bool:
        return method in (cls.CLASS, cls.INSTANCE)
