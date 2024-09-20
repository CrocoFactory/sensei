# sensei
<a href="https://pypi.org/project/sensei/">
<h1 align="center">
<img alt="Logo Banner" src="https://raw.githubusercontent.com/CrocoFactory/sensei/main/branding/logo/transparent_red.png" width="300">
</h1><br>
</a>

[![PyPi Version](https://img.shields.io/pypi/v/sensei)](https://pypi.org/project/sensei/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/sensei?label=downloads)](https://pypi.org/project/sensei/)
[![License](https://img.shields.io/github/license/CrocoFactory/sensei.svg)](https://pypi.org/project/sensei/)
[![Last Commit](https://img.shields.io/github/last-commit/CrocoFactory/sensei.svg)](https://pypi.org/project/sensei/)
[![Development Status](https://img.shields.io/pypi/status/sensei)](https://pypi.org/project/sensei/)

The python framework, providing fast and robust way to build client-side API wrappers.
                           
- **[Maintain](https://www.patreon.com/user/membership?u=142083211)**
- **[Bug reports](https://github.com/CrocoFactory/sensei/issues)**

Source code is made available under the [MIT License](LICENSE).  
                   
# Quick Overview

Here is example of OOP style.

```python
from typing import Annotated
from httpx import Response
from sensei import Router, Query, Path, APIModel, Header, Args
from sensei.cases import pascal_case

router = Router('https://reqres.in/api', header_case=pascal_case)


class User(APIModel):
    email: str
    id: int
    first_name: str
    last_name: str
    avatar: str

    @classmethod
    @router.get('/users')
    def query(
            cls,
            page: Annotated[int, Query(1)],
            per_page: Annotated[int, Query(3, le=7)],
            bearer_token: Annotated[str, Header('secret', le=10)],
    ) -> list["User"]:
        ...

    @staticmethod
    @query.initializer()
    def _query_in(args: Args) -> Args:
        args.headers['Hello-World'] = 'hello world'
        return args

    @staticmethod
    @query.finalizer()
    def _query_out(
            response: Response,
    ) -> list["User"]:
        json = response.json()
        users = [User(**user) for user in json['data']]
        return users

    @classmethod
    @router.get('/users/{id_}')
    def get(cls, id_: Annotated[int, Path(alias='id')]) -> "User":
        ...

    @staticmethod
    @get.finalizer
    def _get_out(response: Response) -> "User":
        json = response.json()
        return User(**json['data'])


users = User.query(per_page=7)
user_id = users[0].id
user = User.get(user_id)
print(user == users[0])
```

Example of functional style.

```python
from typing import Annotated
from sensei import Router, Path, APIModel

router = Router('https://pokeapi.co/api/v2/')


class Pokemon(APIModel):
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
pip install git+https://github.com/CrocoFactory/sensei.git
```