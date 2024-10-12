import datetime
from abc import ABC, abstractmethod
from typing import Annotated, Literal, Any, Union, List

from pydantic import BaseModel, EmailStr
from typing_extensions import Self

from sensei import Query, Path, Body


class UserCredentials(BaseModel):
    email: EmailStr
    password: str


class BaseUser(ABC):
    email: str
    id: int
    first_name: str
    last_name: str
    avatar: str

    @classmethod
    @abstractmethod
    def list(
            cls,
            page: Annotated[int, Query(1)] = 1,
            per_page: Annotated[int, Query(3, le=7)] = 3
    ) -> list[Self]:
        ...

    @classmethod
    @abstractmethod
    def get(cls, id_: Annotated[int, Path(alias='id')]) -> Self: ...

    @abstractmethod
    def delete(self) -> Self: ...

    @abstractmethod
    def login(self) -> str: ...

    @abstractmethod
    def update(
            self,
            name: Annotated[str, Query()],
            job: Annotated[str, Query()]
    ) -> datetime.datetime:
        ...

    @abstractmethod
    def change(
            self,
            name: Annotated[str, Query()],
            job: Annotated[str, Query()]
    ) -> bytes:
        ...

    @classmethod
    @abstractmethod
    def sign_up(
            cls,
            user: Annotated[UserCredentials, Body(embed=True, media_type='application/x-www-form-urlencoded')]
    ) -> str:
        ...

    @classmethod
    @abstractmethod
    def allowed_http_methods(cls) -> List[str]: ...

    @abstractmethod
    def model_dump(
            self,
            *,
            mode: Union[Literal['json', 'python'], str] = 'python',
            by_alias: bool = False,
            exclude_unset: bool = False,
            exclude_defaults: bool = False,
            exclude_none: bool = False,
    ) -> dict[str, Any]:
        pass

    @classmethod
    def test_validate(cls, obj: Self) -> bool:
        result = obj.model_dump(mode='json').keys()
        desired = cls.__annotations__.keys()
        return isinstance(obj, cls) and result == desired
