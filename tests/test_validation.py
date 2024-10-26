from typing import Annotated

import pytest
from httpx import HTTPStatusError, Response
from pydantic import ValidationError
from typing_extensions import Self

from sensei import APIModel, Body, Form, File


class TestValidation:
    def test_response_types(self, router):
        @router.model()
        class _ValidationModel(APIModel):
            @staticmethod
            @router.get('/test1')
            def test() -> Self: ...

            @staticmethod
            @router.get('/test2')
            def test2() -> list[Self]: ...

            @staticmethod
            @router.get('/test3')
            def test3() -> set: ...

        with pytest.raises(ValueError):
            _ValidationModel.test()

        with pytest.raises(ValueError):
            _ValidationModel.test2()

        with pytest.raises(ValueError):
            _ValidationModel.test3()

    def test_args_validation(self, router):
        @router.model()
        class _ValidationModel(APIModel):
            @router.delete('/users/{id_}')
            def delete(self) -> Self: ...

        with pytest.raises(ValueError):
            print(_ValidationModel().delete())

    def test_raise_for_status(self, router, base_maker, sync_maker):
        base = base_maker(router)
        model = sync_maker(router, base)

        with pytest.raises(HTTPStatusError):
            model.get(0)

    def test_body_validation(self, router):
        @router.model()
        class _ValidationModel(APIModel):
            @classmethod
            @router.post('/users/{id_}')
            def create(cls, body1: Annotated[dict, Body(embed=False)],
                       body2: Annotated[dict, Body(embed=False)]) -> Self: ...

            @classmethod
            @router.post('/users/{id_}')
            def create2(cls, body1: Annotated[dict, Body(embed=False)],
                        body2: Annotated[dict, Body(embed=True)]) -> Self: ...

            @classmethod
            @router.post('/users/{id_}')
            def create3(cls, body1: Annotated[dict, Body(embed=True)],
                        body2: Annotated[dict, Body(embed=False)]) -> Self: ...

            @classmethod
            @router.post('/users/{id_}')
            def create4(cls, body1: Annotated[dict, Body()], body2: Annotated[dict, Form()]) -> Self: ...

            @classmethod
            @router.post('/users/{id_}')
            def create5(cls, body1: Annotated[dict, File(embed=False)],
                        body2: Annotated[dict, Form(embed=False)]) -> Self: ...

            @classmethod
            @router.post('/users/{id_}')
            def create6(cls, body1: Annotated[dict, Form(embed=False)],
                        body2: Annotated[dict, Form(embed=False)]) -> Self: ...

        with pytest.raises(ValueError):
            _ValidationModel.create(body1={}, body2={})

        with pytest.raises(ValueError):
            _ValidationModel.create2(body1={}, body2={})

        with pytest.raises(ValueError):
            _ValidationModel.create3(body1={}, body2={})

        with pytest.raises(ValueError):
            _ValidationModel.create4(body1={}, body2={})

        with pytest.raises(ValueError):
            _ValidationModel.create5(body1={}, body2={})

        with pytest.raises(ValueError):
            _ValidationModel.create6(body1={}, body2={})

    def test_response_validation(self, router):
        @router.get('/users')
        def get_users() -> str: ...

        @get_users.finalize()
        def _finalize_users(response: Response) -> int: 
            return 1

        with pytest.raises(ValidationError):
            get_users()
