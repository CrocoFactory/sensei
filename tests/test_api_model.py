from typing import Any, Annotated
from httpx import Response
from sensei import APIModel, Args, snake_case, camel_case, pascal_case, kebab_case, header_case, Cookie, Body, Header


class TestAPIModel:
    def test_str(self):
        class Validation(APIModel):
            attr: int

        obj = Validation(attr=1)
        assert str(obj) == "Validation(attr=1)"

    def test_hooks(self, router, base_maker):
        @router.model()
        class Base(APIModel):
            def __finalize_json__(self, json: dict[str, Any]) -> dict[str, Any]:
                return json['data']

            def __prepare_args__(self, args: Args) -> Args:
                args.headers['X-Token'] = 'secret_token'
                return args

            def __body_case__(self, s: str) -> str:
                return camel_case(s)

            @staticmethod
            def __query_case__(s: str) -> str:
                return pascal_case(s)

            def __header_case__(self, s: str) -> str:
                return kebab_case(s)

            def __cookie_case__(self, s: str) -> str:
                return header_case(s)

            def __response_case__(self, s: str) -> str:
                return snake_case(s)

        class Validation(Base):
            @classmethod
            @router.patch('/users/{id_}', skip_finalizer=True)
            def update(
                    cls,
                    id_: int,
                    my_cookie: Annotated[str, Cookie()],
                    my_body: Annotated[str, Body()],
                    my_extra: Annotated[str, Body(alias='My-Extra')],
                    x_token: Annotated[str, Header()],
            ) -> dict: ...

            @classmethod
            @update.prepare()
            def _get_in(cls, args: Args) -> Args:
                assert args.cookies.get('My-Cookie')
                assert args.json_.get('myBody')
                assert args.headers.get('x-token')
                assert args.json_.get('My-Extra')
                return args

            @classmethod
            @update.finalize
            def _get_out(cls, response: Response) -> dict:
                json_ = response.json()
                for key in json_:
                    assert snake_case(key) == key
                return json_

        res = Validation.update(1, 'cookie', 'body', 'extra', 'header')
        assert isinstance(res, dict)
