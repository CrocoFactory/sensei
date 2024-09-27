import datetime
import pytest
import respx
import jwt
from pydantic_core import ValidationError
from tests.base_user import BaseUser
from tests.mock_api import mock_api, SECRET_TOKEN, JWT_ALGORITHM


class TestSync:
    @pytest.fixture
    def user_model(self, model_base, sync_maker) -> type[BaseUser]:
        return sync_maker(model_base)

    def test_get(self, user_model):
        user = user_model.get(1)
        assert user_model.test_validate(user)

    def test_list(self, user_model):
        users = user_model.list(per_page=6)
        assert all(user_model.test_validate(user) for user in users)

        with pytest.raises(ValidationError):
            user_model.list(per_page=9)

    def test_delete(self, user_model):
        user = user_model.get(1)
        assert user_model.test_validate(user.delete())

        user = user_model.get(1)
        user.id = -100

        with pytest.raises(ValidationError):
            user.delete()

    def test_login(self, user_model, base_url):
        user = user_model.get(1)

        with respx.mock() as mock:
            mock_api(mock, base_url)
            token = user.login()

        assert isinstance(token, str)

        payload = jwt.decode(token, SECRET_TOKEN, algorithms=JWT_ALGORITHM)
        assert payload['sub'] == user.email

    def test_update(self, user_model):
        user = user_model.get(1)

        res = user.update(name="Brandy", job="Data Scientist")
        assert user.first_name == "Brandy"
        assert isinstance(res, datetime.datetime)
