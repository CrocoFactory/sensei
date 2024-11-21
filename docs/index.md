# sensei
<a href="https://pypi.org/project/sensei/">
<h1 align="center">
<img alt="Logo Banner" src="https://raw.githubusercontent.com/CrocoFactory/.github/main/branding/sensei/logo/bookmark_transparent.svg" width="300">
</h1><br>
</a>

*Build robust HTTP Requests and best API clients with minimal implementation*

[![Python versions](https://img.shields.io/pypi/pyversions/sensei?color=%23F94526)](https://pypi.org/project/sensei/)
[![PyPi Version](https://img.shields.io/pypi/v/sensei?color=%23F94526)](https://pypi.org/project/sensei/)
[![Coverage](https://raw.githubusercontent.com/CrocoFactory/sensei/main/badges/coverage.svg)](https://pypi.org/project/sensei/)

The Python framework that provides a quick way to build robust HTTP requests and best API clients. Use type hints, to build requests, with
little or no implementation.

---

**Documentation:** [https://sensei.crocofactory.dev](https://sensei.crocofactory.dev)

**Source code:** [https://github.com/CrocoFactory/sensei](https://github.com/CrocoFactory/sensei)

---

<a href="https://pypi.org/project/sensei/">
<p align="center">
<img alt="Mindmap" src="https://raw.githubusercontent.com/CrocoFactory/sensei/main/assets/mindmap.svg" height="350px">
</p><br>
</a>
    
There are key features provided by `sensei`:

- **Fast:** Do not write any request-handling code, dedicate responsibility to the function's interface(signature) 🚀
- **Short:** Avoid code duplication 🧹 
- **Sync/Async:** Implement sync and async quickly, without headaches ⚡
- **Robust:** Auto validation data before and after request 🛡️️

## First Request

Do you want to see the simplest and most robust HTTP Request? He's already here!

```python
from typing import Annotated
from sensei import Router, Path, APIModel

router = Router('https://pokeapi.co/api/v2/')


class Pokemon(APIModel):
    name: str
    id: int
    height: int
    weight: int


@router.get('/pokemon/{name}')
def get_pokemon(name: Annotated[str, Path(max_length=300)]) -> Pokemon:
    pass


pokemon = get_pokemon(name="pikachu")
print(pokemon)  # Pokemon(name='pikachu' id=25 height=4 weight=60)
```

Didn't it seem to you that the function doesn't contain the code? **Sensei writes it instead of you!** 

Moreover, Sensei abstracts away much of the manual work, letting developers focus on function signatures while the framework
handles the API logic and data validation. This enables a declarative style for your apps.

The example of [First Request](#first-request) demonstrates a simple and robust HTTP request using the Sensei framework.
Here's the key breakdown of the process:

#### 1. Importing Dependencies:

- `Router` manages API endpoints and routing.
- `Path` specifies and validates route parameters.
- `APIModel` defines models for structuring API responses (similar to `pydantic.BaseModel`).

#### 2. Creating the Router:

The `Router` is initialized with the base URL of the *PokéAPI*. All subsequent requests will use this as the base path.

#### 3. Defining the Model:

The `Pokemon` class represents the data structure for a Pokémon, with fields like `name`, `id`, `height`, and `weight`.
It inherits from `APIModel`, which provides validation and serialization.

#### 4. Creating the Endpoint:

The `get_pokemon` function is a routed function decorated with `@router.get`, defining a GET request for
`/pokemon/{name}`.
This uses `Annotated` to ensure that `name` is a string and adheres to the validation rule (max length of 300).

#### 5. Making the Request:

By calling `get_pokemon(name="pikachu")`, Sensei automatically handles validation, makes the HTTP request,
and maps the API response into the `Pokemon` model. The code omits the function body since Sensei handles calls through
the function's signature.

## Comparison

**Sensei** 👍: It provides a high level of abstraction. Sensei simplifies creating API wrappers, offering decorators for 
easy routing, data validation, and automatic mapping of API responses to models. This reduces boilerplate and improves 
code readability and maintainability.

**Bare HTTP Client** 👎: A bare HTTP client like `requests` or `httpx` requires manually managing requests, 
handling response parsing, data validation, and error handling. You have to write repetitive code for each endpoint.

## OOP Style

There is a wonderful OOP approach proposed by Sensei:

```python
class User(APIModel):
    email: EmailStr
    id: PositiveInt
    first_name: str
    last_name: str
    avatar: AnyHttpUrl

    @classmethod
    @router.get('/users')
    def query(
            cls,
            page: Annotated[int, Query()] = 1,
            per_page: Annotated[int, Query(le=7)] = 3
    ) -> list[Self]:
        pass

    @classmethod
    @router.get('/users/{id_}')
    def get(cls, id_: Annotated[int, Path(alias='id')]) -> Self: 
        pass

    @router.post('/token')
    def login(self) -> str: 
        pass

    @login.prepare
    def _login_in(self, args: Args) -> Args:
        args.json_['email'] = self.email
        return args

    @login.finalize
    def _login_out(self, response: Response) -> str:
        return response.json()['token']

user = User.get(1)
user.login() # User(id=1, email="john@example.com", first_name="John", ...)
```

When Sensei doesn't know how to handle a request, you can do it yourself, using preprocessing as `prepare` and 
postprocessing as `finalize`

## Installing
To install `sensei` from PyPi, you can use that:

```shell
pip install sensei
```

To install `sensei` from GitHub, use that:

```shell
pip install git+https://github.com/CrocoFactory/sensei.git
```