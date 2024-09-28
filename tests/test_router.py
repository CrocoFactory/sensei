import pytest
from typing import Annotated, Any
from sensei import Client, Manager, Router, Path, Query, Header, Cookie, Args, Body


class TestRouter:
    def test_client_validation(self, sync_maker, base_maker, base_url):
        def validate(client: Client):
            manager = Manager(client)
            router = Router(host=base_url, manager=manager)
            base = base_maker(router)
            model = sync_maker(router, base)

            with pytest.raises(ValueError):
                model.get(1)

        client1 = Client(host='https://google.com')
        validate(client1)
        client2 = Client(host=base_url, port=3000)
        validate(client2)

    def test_function_style(self, base_url):
        def __finalize_json__(json: dict[str, Any]) -> dict[str, Any]:
            return json['data']

        router = Router(host=base_url, __finalize_json__=__finalize_json__)

        @router.get('/users')
        def query(page: int = 1, per_page: Annotated[int, Query(le=7)] = 3) -> list[dict]: ...

        @router.get('/users/{id_}')
        def get(id_: Annotated[int, Path(alias='id')]) -> dict: ...

        keys = {'email', 'id', 'first_name', 'last_name', 'avatar'}
        assert set(query(per_page=4)[0].keys()) == keys
        assert set(get(1).keys()) == keys

    def test_params(self, router, base_url):
        @router.get('/users/{id_}')
        def get(
                email: str,
                cookie: Annotated[str, Cookie()],
                body: Annotated[str, Body()],
                id_: Annotated[int, Path(alias='id')],
                x_token: Annotated[str, Header()],
        ) -> str: ...

        @get.prepare()
        def _get_in(args: Args) -> Args:
            assert args.url == '/users/1'
            assert args.params.get('email')
            assert args.cookies.get('cookie')
            assert args.json_.get('body')
            assert args.headers.get('X-Token')
            return args

        res = get('email', 'cookie', 'body', 1, 'xtoken')  # type: ignore
        assert isinstance(res, str)

    def test_formatting(self):
        router = Router(host='https://domain.com:{port}/sumdomain', port=3000)
        assert str(router.base_url) == 'https://domain.com:3000/sumdomain'
        router.port = 4000
        assert str(router.base_url) == 'https://domain.com:4000/sumdomain'
