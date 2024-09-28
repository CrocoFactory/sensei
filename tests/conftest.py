import asyncio
import datetime
import pytest
from typing import Any, Callable, Annotated
from httpx import Response
from pydantic import EmailStr, PositiveInt, AnyHttpUrl
from typing_extensions import Self
from .base_user import BaseUser
from sensei import Router, APIModel, Args, snake_case, Query, Path, format_str, Body


@pytest.fixture(scope="session")
def base_url() -> str:
    return 'https://reqres.in/api'


@pytest.fixture()
def router(base_url) -> Router:
    router = Router(base_url)
    return router


@pytest.fixture()
def base_maker() -> Callable[[Router], type[APIModel]]:
    def model_base(router) -> type[APIModel]:
        @router.model()
        class BaseModel(APIModel):
            def __finalize_json__(self, json: dict[str, Any]) -> dict[str, Any]:
                return json['data']

            def __prepare_args__(self, args: Args) -> Args:
                args.headers['X-Token'] = 'secret_token'
                return args

            def __response_case__(self, s: str) -> str:
                return snake_case(s)

        return BaseModel
    return model_base


@pytest.fixture
def sync_maker() -> Callable[[Router, type[APIModel]], type[BaseUser]]:
    def make_model(router: Router, base: type[APIModel]) -> type[BaseUser]:
        class User(base, BaseUser):
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
            ) -> list[Self]:
                ...

            @classmethod
            @router.get('/users/{id_}')
            def get(cls, id_: Annotated[int, Path(alias='id')]) -> Self: ...

            @router.delete('/users/{id_}')
            def delete(self) -> Self: ...

            @delete.prepare
            def _delete_in(self, args: Args) -> Args:
                url = args.url
                url = format_str(url, {'id_': self.id})
                args.url = url
                return args

            @router.post('/token')
            def login(self) -> str: ...

            @login.prepare
            def _login_in(self, args: Args) -> Args:
                args.json_['email'] = self.email
                return args

            @login.finalize
            def _login_out(self, response: Response) -> str:
                return response.json()['token']

            @router.patch('/users/{id_}', skip_finalizer=True)
            def update(
                    self,
                    name: str,
                    job: str
            ) -> datetime.datetime:
                ...

            @update.prepare
            def _update_in(self, args: Args) -> Args:
                args.url = format_str(args.url, {'id_': self.id})
                return args

            @update.finalize()
            def _update_out(self, response: Response) -> datetime.datetime:
                json_ = response.json()
                result = datetime.datetime.strptime(json_['updated_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
                self.first_name = json_['name']
                return result

            @router.put('/users/{id_}', skip_finalizer=True)
            def change(
                    self,
                    name: Annotated[str, Query()],
                    job: Annotated[str, Query()]
            ) -> bytes:
                ...

            @change.prepare
            def _change_in(self, args: Args) -> Args:
                args.url = format_str(args.url, {'id_': self.id})
                return args

        return User
    return make_model


@pytest.fixture
def async_maker() -> Callable[[Router, type[APIModel]], type[BaseUser]]:
    def make_model(router: Router, base: type[APIModel]) -> type[BaseUser]:
        class User(base, BaseUser):
            email: EmailStr
            id: PositiveInt
            first_name: str
            last_name: str
            avatar: AnyHttpUrl

            @classmethod
            @router.get('/users')
            async def list(
                    cls,
                    page: Annotated[int, Query()] = 1,
                    per_page: Annotated[int, Query(le=7)] = 3
            ) -> list[Self]:
                ...

            @classmethod
            @router.get('/users/{id_}')
            async def get(cls, id_: Annotated[int, Path(alias='id')]) -> Self: ...

            @router.delete('/users/{id_}')
            async def delete(self) -> Self: ...

            @delete.prepare
            async def _delete_in(self, args: Args) -> Args:
                url = args.url
                url = format_str(url, {'id_': self.id})
                args.url = url
                return args

            @router.post('/token')
            async def login(self) -> str: ...

            @login.prepare
            async def _login_in(self, args: Args) -> Args:
                args.json_['email'] = self.email
                return args

            @login.finalize
            async def _login_out(self, response: Response) -> str:
                return response.json()['token']

            @router.patch('/users/{id_}', skip_finalizer=True)
            async def update(
                    self,
                    name: str,
                    job: str
            ) -> datetime.datetime:
                ...

            @update.prepare
            async def _update_in(self, args: Args) -> Args:
                args.url = format_str(args.url, {'id_': self.id})
                await asyncio.sleep(1.5)
                return args

            @update.finalize
            async def _update_out(self, response: Response) -> datetime.datetime:
                json_ = response.json()
                result = datetime.datetime.strptime(json_['updated_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
                await asyncio.sleep(1.5)
                self.first_name = json_['name']
                return result

            @router.put('/users/{id_}', skip_finalizer=True)
            async def change(
                    self,
                    name: Annotated[str, Query()],
                    job: Annotated[str, Query()]
            ) -> bytes:
                ...

            @change.prepare
            def _change_in(self, args: Args) -> Args:
                args.url = format_str(args.url, {'id_': self.id})
                return args

        return User
    return make_model

