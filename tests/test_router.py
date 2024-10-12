from typing import Annotated, Any

import pytest

from sensei import Client, Manager, Router, Path, Query, Header, Cookie, Args, Body, Form, File


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
        client3 = Client(host=f'{base_url}//')
        validate(client3)

        manager = Manager(Client(host=f'{base_url}/'))
        router = Router(host=base_url, manager=manager)
        base = base_maker(router)
        model = sync_maker(router, base)
        model.get(1)

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
        preparer_executed = False

        def validate(__dict: dict, key: str, len_: int = 1) -> None:
            assert (__dict.get(key) and len(__dict) == len_)

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
            nonlocal preparer_executed

            assert args.url == '/users/1'
            validate(args.params, 'email')
            validate(args.json_, 'body')
            validate(args.headers, 'X-Token')

            preparer_executed = True

            return args

        get('email', 'cookie', 'body', 1, 'xtoken')  # type: ignore

        assert preparer_executed
        preparer_executed = False

        @router.get('/users')
        def get(
                form: Annotated[str, Form()],
                form2: Annotated[str, Body(media_type="multipart/form-data")],
                my_file: Annotated[str, File()]
        ) -> str: ...

        @get.prepare()
        def _get_in(args: Args) -> Args:
            nonlocal preparer_executed

            validate(args.data, 'form', 2)
            validate(args.data, 'form2', 2)
            validate(args.files, 'my_file')

            preparer_executed = True

            return args

        get('form', 'form2', 'file')
        assert preparer_executed

    def test_media_type(self, router, base_url):
        preparer_executed = False
        media_type = "application/xml"

        @router.get('/users')
        def get(
                my_xml: Annotated[str, Body(media_type=media_type)],
        ) -> str: ...

        @get.prepare()
        def _get_in(args: Args) -> Args:
            nonlocal preparer_executed
            assert args.headers['Content-Type'] == media_type
            assert args.data['my_xml'] == '<xml></xml>'

            preparer_executed = True
            return args

        get(my_xml='<xml></xml>')
        assert preparer_executed

    def test_formatting(self):
        router = Router(host='https://domain.com:{port}/sumdomain', port=3000)
        assert str(router.base_url) == 'https://domain.com:3000/sumdomain'
        router.port = 4000
        assert str(router.base_url) == 'https://domain.com:4000/sumdomain'

    def test_props(self):
        client = Client(host='https://google.com', port=3000)
        manager = Manager(client)
        router = Router(manager=manager, host='https://google.com', port=3000)

        @router.get('/validate')
        def validate() -> None:
            ...

        router.port = 4000
        router.manager = Manager(Client(host='https://google.com', port=4000))

        @validate.prepare()
        def _validate_in(args: Args) -> Args:
            raise ReferenceError

        try:
            validate()
        except ReferenceError:
            pass

        router.port = None
