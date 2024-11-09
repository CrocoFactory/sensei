from datetime import datetime
from typing import Annotated, Any, Optional

import pytest
from pydantic import EmailStr, PositiveInt, AnyHttpUrl
from typing_extensions import assert_type

from sensei import Client, Manager, Router, Path, Query, Header, Cookie, Args, Body, Form, File, APIModel


class TestRouter:
    def test_client_validation(self, sync_maker, base_maker, base_url):
        def validate(client: Client):
            manager = Manager(client)
            router = Router(host=base_url, manager=manager)
            base = base_maker(router)
            model = sync_maker(router, base)

            with pytest.raises(ValueError):
                model.get(1)

        client1 = Client(base_url='https://google.com')
        validate(client1)
        client3 = Client(base_url=f'{base_url}//')
        validate(client3)

        manager = Manager(Client(base_url=f'{base_url}/'))
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

        def validate(dict_: dict, key: str, len_: int = 1) -> None:
            assert (dict_.get(key) and len(dict_) == len_)

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
                my_file: Annotated[bytes, File()]
        ) -> str: ...

        @get.prepare()
        def _get_in(args: Args) -> Args:
            nonlocal preparer_executed

            validate(args.data, 'form', 2)
            validate(args.data, 'form2', 2)
            validate(args.files, 'my_file')

            preparer_executed = True

            return args

        get('form', 'form2', b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x02\xb8\x00\x00\x03\x10\x08\x06\x00\x00\x00\xcc\xf8\x16\x18\x00\x00\x0cNiCCPICC02\x04\x8a\n\x08\xb8E9uF\x80\x00\x01\x02\x04\x08\x10 \xd0\xb6\xc0\xff\x03$\xc0\xf7*\xd5\xc0\xb9%\x00\x00\x00\x00IEND\xaeB`\x82')
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

    def test_old_self(self, router, base_url, base_maker):
        base = base_maker(router)

        class User(base):
            email: EmailStr
            id: PositiveInt
            first_name: str
            last_name: str
            avatar: AnyHttpUrl

            @classmethod
            @router.get('/users')
            def list(
                    cls,
                    page: Annotated[int, Query()] = 1,
                    per_page: Annotated[int, Query(le=7)] = 3
            ) -> list["User"]:
                ...

            @classmethod
            @router.get('/users/{id_}')
            def get(cls, id_: Annotated[int, Path(alias='id')]) -> "User": ...

        user = User.get(1)
        assert_type(user, User)
        users = User.list()
        
        for user in users:
            assert_type(user, User)

    def test_formatting(self):
        router = Router(host='https://domain.com:{port}/sumdomain', port=3000)
        assert str(router.base_url) == 'https://domain.com:3000/sumdomain'
        router._port = 4000
        assert str(router.base_url) == 'https://domain.com:4000/sumdomain'

    def test_props(self):
        client = Client(base_url='https://google.com:3000')
        manager = Manager(client)
        router = Router(manager=manager, host='https://google.com', port=3000)

        @router.get('/validate')
        def validate() -> None:
            ...

        router._port = 4000
        router.manager = Manager(Client(base_url='https://google.com:4000'))

        @validate.prepare()
        def _validate_in(args: Args) -> Args:
            raise ReferenceError

        try:
            validate()
        except ReferenceError:
            pass

        router._port = None

    def test_unset_params(self, base_url, router):
        router = Router(base_url, __finalize_json__=lambda x: x['data'])

        class Company(APIModel):
            name: Optional[str] = None
            location: Optional[str] = None

        class Job(APIModel):
            company: Optional[Company] = None
            start: datetime = None

        class User(APIModel):
            email: EmailStr
            id: PositiveInt
            first_name: str
            last_name: str
            job: Optional[Job] = None
            avatar: AnyHttpUrl

        @router.get('/users')
        def list_users(
                page: Annotated[int, Query()] = 1,
                per_page: Annotated[int, Query(le=7)] = 3,
                job: Optional[Job] = None,
        ) -> list[User]:
            ...

        def serialize_args(*args, **kwargs) -> dict[str, Any]:
            serialized = {}

            @list_users.prepare()
            def _prepare1(args: Args) -> Args:
                nonlocal serialized
                serialized = args.model_dump()
                return args

            list_users(*args, **kwargs)
            return serialized

        args = serialize_args()
        assert 'job' not in args['params']

        job = {'company': {'name': 'Croco'}}
        args = serialize_args(job=job)
        assert args['params']['job'] == job