from typing import Any, Annotated

from httpx import Response

from sensei import APIModel, Args, snake_case, camel_case, kebab_case, header_case, Cookie, Body, Header, \
    constant_case, Router


class TestAPIModel:
    def test_str(self):
        class Validation(APIModel):
            attr: int

        obj = Validation(attr=1)
        assert str(obj) == "Validation(attr=1)"

    def test_hooks(self, base_url, base_maker):
        router = Router(base_url, default_case=camel_case)

        class Base(APIModel):
            def __finalize_json__(self, json: dict[str, Any]) -> dict[str, Any]:
                return json['data']

            def __prepare_args__(self, args: Args) -> Args:
                args.headers['X-Token'] = 'secret_token'
                return args

            def __header_case__(self, s: str) -> str:
                return kebab_case(s)

            @staticmethod
            def __response_case__(s: str) -> str:
                return snake_case(s)

        @router.model()
        class Validation(Base):
            def __cookie_case__(self, s: str) -> str:
                return header_case(s)
            
            @classmethod
            @router.patch('/users/{id_}', header_case=constant_case, skip_finalizer=True)
            def update(
                    cls,
                    id_: int,
                    my_cookie: Annotated[str, Cookie()],
                    my_body: Annotated[str, Body()],
                    my_extra: Annotated[str, Body(alias='My-Extra')],
                    m_token: Annotated[str, Header()],
            ) -> dict: ...

            @classmethod
            @update.prepare()
            def _get_in(cls, args: Args) -> Args:
                assert args.cookies.get('My-Cookie')
                assert args.json_.get('myBody')
                assert args.headers.get('M_TOKEN')
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

    def test_decorating_methods(self, router, base_maker):
        base = base_maker(router)

        class Model(base):
            def method(self) -> str:
                return 'My Method'

            @router.get('/users')
            def routed(self): ...

        assert getattr(Model.method, 'finalize', None) is None
        assert getattr(Model.routed, 'prepare', None) is not None
        