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

Let's take this request step by step.

### Step 1: Importing Dependencies

```python
from typing import Annotated
from sensei import Router, Path, APIModel
```

**Annotated** is imported from Python's `typing` module, allowing us to add metadata (like *param types*) to variables.

**Router**, **Path**, and **APIModel** are imported from the Sensei framework.

- **Router** helps manage API endpoints and routing.
- **Path** specifies path (route) parameters and defines argument's validation.
- **APIModel** is used to define models for structuring API responses.

### Step 2: Creating a Router

```python
router = Router('https://pokeapi.co/api/v2/')
```

A **Router** instance is created, with the base URL of the *PokéAPI* (`https://pokeapi.co/api/v2/`). This will be the
root path for all subsequent API calls.

### Step 3: Defining the `Pokemon` Model

```python
class Pokemon(APIModel):
    name: str
    id: int
    height: int
    weight: int
```

**Pokemon** is a class that inherits from **APIModel**. This class represents the structure of a Pokémon's data.
The attributes are:

- `name`: a *string*
- `id`: an *integer*
- `height`: an *integer*
- `weight`: an *integer*

/// note | Technical Details
`APIModel` inherits from `BaseModel` of `pydantic` framework. You can apply the principles of `pydantic` for models
in Sensei
///

### Step 4: Defining the `get_pokemon` Endpoint

```python
@router.get('/pokemon/{name}')
def get_pokemon(name: Annotated[str, Path(max_length=300)]) -> Pokemon: ...
```

This function is decorated with `@router.get`, defining it as a GET request for the `/pokemon/{name}` endpoint.

/// tip
If you don't know what are "request", "response" "route", "endpoint", "methods" and other HTTP terms, visit
[HTTP Requests](/learn/http_requests.html)
///

The `{name}` is a *path parameter*, dynamically inserted into the API call.

- `name`: is an argument annotated as a *string* with **Path**, meaning it is a required URL path parameter. Also, in
  **Path** we defined validation, namely checking whether length of name less or equal then 300. **Path** is placed in
  `Annotated` object as metadata.

/// info
**Decorator** is a design pattern that allows you to modify or extend the behavior of functions or methods without
changing their code directly.

In Python they are applied by using the `@decorator` syntax just above a
function definition. In most cases, decorator is some function, taking function and returning modified(decorated)
function
///

Instead of `@router.get`, you can use the other operations(HTTP methods):

* `@router.post`
* `@router.put`
* `@router.delete`
* `@router.patch`
* `@router.head`
* `@router.options`

The function body is omitted because **Sensei** automatically handles the API call and response mapping. This "omitting"
we will call *Interface-driven function* or *Signature-driven function*, because we do not write any code achieving
the result. We dedicate this responsibility to some tool, parsing the function's interface(signature). And according to
it,
tool handles a call automatically.

In this case, the function returns a **Pokemon** object, ensuring that the data fetched from the API matches the *
*Pokemon** model.
The return type we will also call *response type*.

### Step 5: Making the API Call

```python
pokemon = get_pokemon(name="pikachu")
print(pokemon)
```

Let's consider the algorithm of call:

1) Calling `get_pokemon` function with the argument `name="pikachu"`.

2) Collecting arguments, including its names and types, *param types* (e.g. Path, Query, Body, Cookie, Header),
   including
   argument validations placed inside, and return type.

3) Validating input args. In this case `name="pikachu"`

4) Sending HTTP request.

5) Validating and mapping response, according to the return type

### Async Request

If you want to make asynchronous request, the code will be almost the same

```python
import asyncio
from typing import Annotated
from sensei import Router, Path, APIModel

router = Router('https://pokeapi.co/api/v2/')


class Pokemon(APIModel):
    name: str
    id: int
    height: int
    weight: int


@router.get('/pokemon/{name}')
async def get_pokemon(name: Annotated[str, Path(max_length=300)]) -> Pokemon:
    ...


async def main() -> None:
    pokemon = await get_pokemon(name="pikachu")
    print(pokemon)


asyncio.run(main())
```

Only add `async` before `def`!

/// tip
If you don't know what is "concurrency", "parallelism" and what does do "async/await" in Python,
visit [Concurrency/Parallelism](/learn/concurrency_parallelism.html)
///
