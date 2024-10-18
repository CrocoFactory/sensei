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

`Annotated` is imported from Python's `typing` module, allowing us to add metadata (like *param types*) to variables.

`Router`, `Path`, and `APIModel` are imported from the Sensei framework.

- `Router` helps manage API endpoints and routing.
- `Path` specifies path (route) parameters and defines argument's validation.
- `APIModel` is used to define models for structuring API responses.

### Step 2: Creating a Router

```python
router = Router('https://pokeapi.co/api/v2/')
```

A `Router` instance is created, with the base URL of the *PokéAPI* (`https://pokeapi.co/api/v2/`). This will be the
root path for all subsequent API calls.

### Step 3: Defining the `Pokemon` Model

```python
class Pokemon(APIModel):
    name: str
    id: int
    height: int
    weight: int
```

`Pokemon` is a class that inherits from `APIModel`. This class represents the structure of a Pokémon's data.
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

- `name`: is an argument annotated as a *string* with `Path`, meaning it is a required URL path parameter. Also, in
  `Path` we defined validation, namely checking whether length of name less or equal then 300. `Path` is placed in
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

The function body is omitted because **Sensei** automatically handles the API call and response mapping.
In this case, the function returns a `Pokemon` object, ensuring that the data fetched from the API matches the
`Pokemon` model. The return type we will call **response type**.

/// info
This "omitting"
we will call **Interface-driven function** or **Signature-driven function**, because we do not write any code achieving
the result. We dedicate this responsibility to some tool, parsing the function's interface(signature). And according to
it, tool handles a call automatically.
///

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

## API Model

As mentioned earlier, `APIModel` models use the same principles as `BaseModel` models from `pydantic`.
Let’s go over the basics!

### Creating

```python
from sensei import APIModel
from pydantic import EmailStr, NonNegativeInt


class User(APIModel):
    id: NonNegativeInt
    username: str
    email: EmailStr
    age: int = 18
    is_active: bool = True
```

In this `User` model, the fields are:

1. `id`: an integer for the user ID. `NonNegativeInt` ensures that the value >= 0.
2. `username`: a string for the username.
3. `email`: validated by the `EmailStr` type from `pydantic`, ensuring a valid email.
4. `age`: an integer defaulting to 18.
5. `is_active`: a boolean defaulting to True.

/// tip
Value validation is not force type validation.
For example, if you define model with `due_date` and `id` fields of types `datetime` and integer respectively,
as `id` you can pass numerical string and as date you can pass **ISO-8601**, **UTC** and strings of other formats.

```python
from sensei import APIModel
from datetime import datetime


class Task(APIModel):
    id: int
    due_date: datetime


Task(due_date='2024-10-15T15:30:00', id="1")
```

The result will be

```python
Task(id=1
due_date = datetime.datetime(2024, 10, 15, 15, 30))
```

///

### Serializing

To serialize model, you can use `model_dump` method.

```python
user = User(id=1, username="johndoe", email="johndoe@example.com", age=30)
user_data = user.model_dump(mode="json")
user_data
```

```json
{
  "id": 1,
  "username": "johndoe",
  "email": "johndoe@example.com",
  "age": 30,
  "is_active": True
}
```

/// tip
If you use response in another request or want to write it to file, you should serialize it with `mode="json"`.

```python
user_data = user.model_dump(mode="json")
```

For example, if you have some field with `datetime` object, this mode evaluates this time as string.

```python
from sensei import APIModel
from datetime import datetime


class Task(APIModel):
    due_date: datetime
    ...


Task(due_date=datetime(2024, 10, 15, 15, 30)).model_dump(mode="json")
```

The result will be

```json
{
  "date": '2024-10-15T15:30:00',
  ...
}
```

///