# sensei
<a href="https://pypi.org/project/sensei/">
<h1 align="center">
<img alt="Logo Banner" src="https://raw.githubusercontent.com/CrocoFactory/.github/main/branding/sensei/logo/bookmark_transparent.svg" width="300">
</h1><br>
</a>

*Build painless HTTP Requests with minimal implementation*

[![Python versions](https://img.shields.io/pypi/pyversions/sensei?color=%23F94526)](https://pypi.org/project/sensei/)
[![PyPi Version](https://img.shields.io/pypi/v/sensei?color=%23F94526)](https://pypi.org/project/sensei/)
[![Coverage](https://raw.githubusercontent.com/CrocoFactory/sensei/main/badges/coverage.svg)](https://pypi.org/project/sensei/)
           
The Python framework, that provides a quick way to build API wrappers. Use type hints, to build requests, with little or no implementation

---

**Documentation:** [https://sensei.crocofactory.dev](https://sensei.crocofactory.dev)

**Source code:** [https://github.com/CrocoFactory/sensei](https://github.com/CrocoFactory/sensei)

**Maintain:** [https://www.patreon.com/user/...](https://www.patreon.com/user/membership?u=142083211)

---
    
There are key features provided by `sensei`:

- **Fast:** Do not write any request-handling code, dedicate responsibility to the function's interface(signature)
- **Short:** Avoid code duplication. 
- **Sync/Async:** Implement sync and async quickly, without headaches
- **Robust:** Auto validation data before and after request


## Quick Overview

API Wrapper should provide these features for users:

- Provide sync and async code versions
- Validate data before accessing the API.
- Handle RPS (Requests per second) limits.
- Return relevant response

And as a developer, you want to avoid code duplication and make routine things faster. To follow all these principles,
you either violate DRY or have to maintain bad code architecture.

**Sensei is a tool to avoid these issues.**

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
def get_pokemon(name: Annotated[str, Path(max_length=300)]) -> Pokemon: ...


pokemon = get_pokemon(name="pikachu")
print(pokemon)
```

Sensei abstracts away much of the manual work, letting developers focus on function signatures while the framework
handles the API logic and data validation.

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
and maps the API response into the `Pokemon` model. The code omits the function body since Sensei handles call through
the function's signature.

## Installing sensei
To install `sensei` from PyPi, you can use that:

```shell
pip install sensei
```

To install `sensei` from GitHub, use that:

```shell
pip install git+https://github.com/CrocoFactory/sensei.git
```