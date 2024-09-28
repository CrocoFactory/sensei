from enum import Enum


class Hook(Enum):
    JSON_FINALIZER = "__finalize_json__"
    ARGS_PREPARER = "__prepare_args__"

    QUERY_CASE = "__query_case__"
    BODY_CASE = "__body_case__"
    COOKIE_CASE = "__cookie_case__"
    HEADER_CASE = "__header_case__"
    RESPONSE_CASE = "__response_case__"

    @classmethod
    def values(cls) -> list[str]:
        return [member.value for member in cls]
