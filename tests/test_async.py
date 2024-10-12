import datetime

import jwt
import pytest
import respx
from pydantic_core import ValidationError

from tests.base_user import BaseUser, UserCredentials
from tests.mock_api import mock_api, SECRET_TOKEN, JWT_ALGORITHM


class TestAsync:
    @pytest.fixture
    def user_model(self, base_maker, async_maker, router) -> type[BaseUser]:
        base = base_maker(router)
        return async_maker(router, base)

    @pytest.mark.asyncio
    async def test_get(self, user_model):
        user = await user_model.get(1)  # type: ignore
        assert user_model.test_validate(user)

    @pytest.mark.asyncio
    async def test_list(self, user_model):
        users = await user_model.list(per_page=6)  # type: ignore
        assert all(user_model.test_validate(user) for user in users)

        with pytest.raises(ValidationError):
            await user_model.list(per_page=9)  # type: ignore

    @pytest.mark.asyncio
    async def test_delete(self, user_model):
        user = await user_model.get(1)  # type: ignore
        assert user_model.test_validate(await user.delete())

        user = await user_model.get(1)  # type: ignore
        user.id = -100

        with pytest.raises(ValidationError):
            await user.delete()  # type: ignore

    @pytest.mark.asyncio
    async def test_login(self, user_model, base_url):
        user = await user_model.get(1)  # type: ignore

        async with respx.mock() as mock:
            mock_api(mock, base_url, '/token')
            token = await user.login()  # type: ignore

        assert isinstance(token, str)

        payload = jwt.decode(token, SECRET_TOKEN, algorithms=JWT_ALGORITHM)
        assert payload['sub'] == user.email

    @pytest.mark.asyncio
    async def test_update(self, user_model):
        user = await user_model.get(1)  # type: ignore

        res = await user.update(name="Brandy", job="Data Scientist")  # type: ignore
        assert user.first_name == "Brandy"
        assert isinstance(res, datetime.datetime)

    @pytest.mark.asyncio
    async def test_change(self, user_model):
        user = await user_model.get(1)  # type: ignore
        res = await user.change(name="Brandy", job="Data Scientist")  # type: ignore
        assert isinstance(res, bytes)

    @pytest.mark.asyncio
    async def test_sign_up(self, user_model, base_url):
        email = "helloworld@gmail.com"

        with respx.mock() as mock:
            mock_api(mock, base_url, '/register')
            token = await user_model.sign_up(UserCredentials(email=email, password="mypassword"))  # type: ignore

        assert isinstance(token, str)

        payload = jwt.decode(token, SECRET_TOKEN, algorithms=JWT_ALGORITHM)
        assert payload['sub'] == email

    @pytest.mark.asyncio
    async def test_allowed_methods(self, user_model):
        methods = sorted(['GET', 'HEAD', 'PUT', 'PATCH', 'POST', 'DELETE'])
        assert methods == sorted(await user_model.allowed_http_methods())  # type: ignore
