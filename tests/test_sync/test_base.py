import pytest
import respx
import jwt
from pydantic_core import ValidationError
from tests.base_user import BaseUser
from tests.mock_api import mock_api, SECRET_TOKEN


def test_get(base_model: type[BaseUser]):
    # Tests: class method, self
    user = base_model.get(1)
    assert base_model.validate(user)
    

def test_list(base_model: type[BaseUser]):
    # Tests: class method, list[Self]
    users = base_model.list(per_page=6)
    assert all(base_model.validate(user) for user in users)

    with pytest.raises(ValidationError):
        base_model.list(per_page=9)


def test_delete(base_model: type[BaseUser]):
    # Tests: instance method, Self
    user = base_model.get(1)
    assert base_model.validate(user.delete())

    user = base_model.get(1)
    user.id = -100

    with pytest.raises(ValidationError):
        user.delete()


def test_login(base_model, base_url):
    # Tests: POST, finalize, prepare
    user = base_model.get(1)

    with respx.mock() as mock:
        mock_api(mock, base_url)
        token = user.login()

    assert isinstance(token, str)
        
    payload = jwt.decode(token, SECRET_TOKEN, algorithms='HS256')
    assert payload['sub'] == user.email
