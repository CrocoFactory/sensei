# sensei
[![PyPi Version](https://img.shields.io/pypi/v/sensei)](https://pypi.org/project/sensei/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/sensei?label=downloads)](https://pypi.org/project/sensei/)
[![License](https://img.shields.io/github/license/blnkoff/sensei.svg)](https://pypi.org/project/sensei/)
[![Last Commit](https://img.shields.io/github/last-commit/blnkoff/sensei.svg)](https://pypi.org/project/sensei/)
[![Development Status](https://img.shields.io/pypi/status/sensei)](https://pypi.org/project/sensei/)

The python framework, providing fast and robust way to build client-side API wrappers.
         
- **[Bug reports](https://github.com/blnkoff/sensei/issues)**

Source code is made available under the [MIT License](LICENSE)
                   
# Quick Overview

Here is example of code.

```python
from typing import Annotated
from httpx import Response
from sensei import Router, Query, Path, BaseModel

router = Router('https://reqres.in/api')


class User(BaseModel):
    email: str
    id: int
    first_name: str
    last_name: str
    avatar: str


@router.get('/users')
def get_users(
        page: Annotated[int, Query(1)],
        per_page: Annotated[int, Query(3, le=7)],
) -> list[User]:
    ...


@get_users.finalizer
def _get_users_out(
        response: Response,
) -> list[User]:
    json = response.json()
    users = [User(**user) for user in json['data']]
    return users


@router.get('/users/{id_}')
def get_user(id_: Annotated[int, Path(alias='id')]) -> User:
    ...


@get_user.finalizer
def _get_user_out(response: Response) -> User:
    json = response.json()
    return User(**json['data'])
        

users = get_users(per_page=7)
user_id = users[1].id

user = get_user(user_id)
print(user == users[1])
```

Another example

```python
from typing import Annotated
from sensei import Router, Path, BaseModel

router = Router('https://pokeapi.co/api/v2/')


class Pokemon(BaseModel):
    name: str
    id: int
    height: int
    weight: int
    types: list


@router.get('/pokemon/{pokemon_name}')
def get_pokemon(
        pokemon_name: Annotated[str, Path()],
) -> Pokemon:
    ...


pokemon = get_pokemon(pokemon_name="pikachu")
print(pokemon)
```

# Installing sensei
To install `sensei` from PyPi, you can use that:

```shell
pip install sensei
```

To install `sensei` from GitHub, use that:

```shell
pip install git+https://github.com/blnkoff/sensei.git
```