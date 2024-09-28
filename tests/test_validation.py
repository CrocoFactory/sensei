import pytest
from httpx import HTTPStatusError
from typing_extensions import Self
from sensei import APIModel


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