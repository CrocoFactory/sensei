import pytest
from typing import Any
from sensei import Router, APIModel, Args, snake_case


@pytest.fixture(scope="session")
def base_url() -> str:
    return 'https://reqres.in/api'


@pytest.fixture()
def router(base_url) -> Router:
    router = Router(base_url)
    return router


@pytest.fixture()
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
