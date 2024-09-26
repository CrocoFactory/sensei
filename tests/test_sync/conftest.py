import pytest
from typing import Annotated
from httpx import Response
from pydantic import EmailStr, PositiveInt, AnyHttpUrl
from typing_extensions import Self
from collections.abc import Callable
from sensei import APIModel, Query, Path, Args, format_str, Router
from tests.base_user import BaseUser


@pytest.fixture
def model_maker(router: Router) -> Callable[[type[APIModel]], type[BaseUser]]:
    def make_model(base: type[APIModel]) -> type[BaseUser]:
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
                    page: Annotated[int, Query(1)] = 1,
                    per_page: Annotated[int, Query(3, le=7)] = 3
            ) -> list[Self]:
                ...

            @classmethod
            @router.get('/users/{id_}')
            def get(cls, id_: Annotated[int, Path(alias='id')]) -> Self:
                ...

            @router.delete('/users/{id_}')
            def delete(self) -> Self:
                ...

            @delete.prepare
            def _delete_in(self, args: Args) -> Args:
                url = args.url
                url = format_str(url, {'id_': self.id})
                args.url = url
                return args

            @router.post('/token')
            def login(self) -> str:
                ...

            @login.prepare
            def _login_in(self, args: Args) -> Args:
                args.json_['email'] = self.email
                return args

            @login.finalize
            def _login_out(self, response: Response) -> str:
                return response.json()['token']

        return User
    return make_model


@pytest.fixture
def base_model(model_base, model_maker) -> type[BaseUser]:
    return model_maker(model_base)
