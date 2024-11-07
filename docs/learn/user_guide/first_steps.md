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
print(pokemon)
```

/// tip
If you don't know what are "request", "response" "route", "endpoint", "methods" and other HTTP terms, visit
[HTTP Requests](/learn/http_requests.html)
///

Let's take this request step by step.

### Step 1: Importing Dependencies

```python
from typing import Annotated
from sensei import Router, Path, APIModel
```

`Annotated` is imported from Python's `typing` module, allowing us to add metadata (like
[Param Types](/learn/user_guide/params_response.html#param-types)) to variables.

`Router`, `Path`, and `APIModel` are imported from the Sensei framework.

- `Router` helps manage API endpoints and routing.
- `Path` specifies path (route) parameters and defines the argument's validation.
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
`APIModel` inherits from `BaseModel` of [`pydantic`](https://docs.pydantic.dev/) framework. You can apply the principles
of [`pydantic`](https://docs.pydantic.dev/) for models
in Sensei
///

### Step 4: Defining the Routed Function

```python
@router.get('/pokemon/{name}')
def get_pokemon(name: Annotated[str, Path(max_length=300)]) -> Pokemon: 
    pass
```

This function is decorated with `@router.get`, defining it as a GET request for the `/pokemon/{name}` endpoint.

/// info
**Decorator** is a design pattern that allows you to modify or extend the behavior of functions or methods without
changing their code directly.

In Python, they are applied using the `@decorator` syntax just above a
function definition. In most cases, the decorator is some function, taking function and returning modified(decorated)
function
///

The `{name}` is a *path parameter*, dynamically inserted into the API call.

- `name`: is an argument annotated as a *string* with `Path`, meaning it is a required URL path parameter. Also, in
  `Path` we defined validation rules, namely checking whether the length of the name is less or equal then 300. 
  `Path` is placed in `Annotated` object as metadata.
        
#### Routed Function

Instead of `@router.get`, you can use the other operations (HTTP methods):

* `@router.post`
* `@router.put`
* `@router.delete`
* `@router.patch`
* `@router.head`
* `@router.options`

These decorators are called **route decorators** and the result of these decorators is called 
**routed function (method)**. Sometimes, if it is clear from the context that we are talking about a routed function,
we will shorten this name to a **route**.

/// warning
Routed functions must not have the body.
This code will not be executed. Instead of the body, place the `pass` keyword.

```python
@router.get('/pokemon/{name}')
def get_pokemon(name: Annotated[str, Path(max_length=300)]) -> Pokemon:
    pass
```

///

The function body is omitted because **Sensei** automatically handles the API call and response mapping.
In this case, the function returns a `Pokemon` object, ensuring that the data fetched from the API matches the
`Pokemon` model. The return type we will also
call [response type](/learn/user_guide/params_response.html#response-types).

/// info
This "omitting" pattern is called **Interface-driven function** or **Signature-driven function**, because we do not
write any code achieving
the result. We dedicate this responsibility to some tool, parsing the function's interface(signature). According to
it, the tool handles a call automatically. This pattern is the key to how Sensei achieves declarative code style.
///

### Step 5: Making the API Call

```python
pokemon = get_pokemon(name="pikachu")
print(pokemon)
```

Let's consider the algorithm of the call:

1) Calling the `get_pokemon` function with the argument `name="pikachu"`.

2) Collecting the function's return type and arguments, including its names and
   types, [Param Types](/learn/user_guide/params_response.html#param-types),
   such as `Path`, `Query`, `Body`, `Cookie`, `Header`, `File`, and `Form`, including argument validations placed inside
   them.

3) Validating input args. In this case `name="pikachu"`

4) Sending HTTP request.

5) Validating and mapping response, according to the return type

### Async Request

If you want to make an asynchronous request, the code will be almost the same:

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
    pass


async def main() -> None:
    pokemon = await get_pokemon(name="pikachu")
    print(pokemon)


asyncio.run(main())
```

Only add `async` before `def`!

/// tip
If you don't know what are "concurrency", "parallelism" and what does do "async/await" in Python,
visit [Concurrency/Parallelism](/learn/concurrency_parallelism.html)
///

## API Model

As mentioned earlier, `APIModel` models use the same principles as `BaseModel` models from [
`pydantic`](https://docs.pydantic.dev/). You can explore its [documentation](https://docs.pydantic.dev/), to learn info for advanced users. 
To make request with non-scalar input/output values, you definitely need to create models.
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

Models created using `APIModel` have validation.
This means if you pass a value not matching corresponding field constraints, `ValidationError` will be thrown.

??? failure "ValidationError"
    ```python
    User(id=-1, username="user", email="randomstr", age=18.01, is_active=-1)
    ```

    4 validation errors for User
    id
      Input should be greater than or equal to 0 [type=greater_than_equal, input_value=-1, input_type=int]
        For further information visit https://errors.pydantic.dev/2.9/v/greater_than_equal
    email
      value is not a valid email address: An email address must have an @-sign. [type=value_error, input_value='randomstr', input_type=str]
    age
      Input should be a valid integer, got a number with a fractional part [type=int_from_float, input_value=18.01, input_type=float]
        For further information visit https://errors.pydantic.dev/2.9/v/int_from_float
    is_active
      Input should be a valid boolean, unable to interpret input [type=bool_parsing, input_value=-1, input_type=int]
        For further information visit https://errors.pydantic.dev/2.9/v/bool_parsing

In this `User` model, the fields are:

1. `id`: an integer for the user ID. `NonNegativeInt` ensures that the value >= 0.
2. `username`: a string for the username.
3. `email`: validated by the `EmailStr` type from `pydantic`, ensuring a valid email.
4. `age`: an integer defaulting to 18.
5. `is_active`: a boolean defaulting to True.


/// tip
Value validation is not force-type validation.
For example, if you define a model with `id`, `due_date`, and `priority` fields of types `int`, `bool`, and `datetime`
respectively,
you can pass:

- numerical string as `id`
- **ISO-8601**, **UTC** or strings of the other date formats as `due_date`
- `'yes'/'no'`, `'on'/'off'`, `'true'/'false'`, `1/0` etc. as `priority`

```python
from sensei import APIModel
from datetime import datetime


class Task(APIModel):
    id: int
    due_date: datetime
    priority: bool


task = Task(due_date='2024-10-15T15:30:00', id="1", priority="yes")
print(task)
```

The result will be

```python
Task(id=1, due_date=datetime.datetime(2024, 10, 15, 15, 30), priority=True)
```

///

### Validating

#### Constrained Types

In addition to built-in validation like `EmailStr` or `NonNegativeInt`,
you can enforce more specific constraints in your models using **Constrained types**, like `constr` and `conint`.

- `constr`: Enforces restrictions on a string field, like setting a minimum or maximum length,
  or allowing only certain characters.
- `conint`: Enforces restrictions on an integer field, such as minimum and maximum value.

For instance, in the `User` model, you can add constraints for the `username`, `id`, and `age` fields. Here's an updated
version
of the `User` model:

```python
from sensei import APIModel
from pydantic import EmailStr, conint, constr


class User(APIModel):
    id: conint(ge=0)  # (1)!
    username: constr(pattern=r'^\w+$')  # (2)!
    email: EmailStr
    age: conint(ge=14) = 18  # (3)!
    is_active: bool = True
```

1. Ensures id is a non-negative integer
2. Allows only alphanumeric characters and underscores
3. Ensures the age is 14 or older

/// info
There are also many constrained types called by pattern `con<type>`:

- `conset`
- `conbytes`
- `conlist`
- etc...

///

#### Field Types

The same validation rules can also be applied using `Field`. There are two approaches to use it.

/// note | Technical Details
Sensei's [Param Types](/learn/user_guide/params_response.html#param-types), such as `Path`, `Query`, `Cookie`, `Header`,
`Body`, `File`, and `Form` are inherited from
`FieldInfo`,
produced by the `Field` function. All approaches that will be described are applied
to [Param Types](/learn/user_guide/params_response.html#param-types).  
///

##### Annotated

Here’s how you can rewrite the same `User` model using `Annotated`:

```python
from typing import Annotated
from sensei import APIModel
from pydantic import EmailStr, Field


class User(APIModel):
    id: Annotated[int, Field(ge=0)]  # (1)!
    username: Annotated[str, Field(pattern=r'^\w+$')]  # (2)!
    email: EmailStr
    age: Annotated[int, Field(18, ge=14)]  # (3)! 
    is_active: bool = True
```

1. Same as `conint(ge=0)`
2. Same as `constr(pattern=r'^\w+$')`
3. Same as `conint(ge=14)`

Setting the default value of age can be achieved in different ways:

1. Passing default value as an argument to `Field`

    ```python
    age: Annotated[int, Field(18, ge=14)]  
    ```

2. Or a familiar way

    ```python
    age: Annotated[int, Field(ge=14)] = 18  
    ```

##### Directly

For simplicity, you can use `Field()` directly, without `Annotated`.

Here’s how you can rewrite the `User` model:

```python
from sensei import APIModel
from pydantic import EmailStr, Field


class User(APIModel):
    id: int = Field(ge=0)  # (1)!
    username: str = Field(regex=r'^\w+$')  # (2)!
    email: EmailStr
    age: int = Field(18, ge=14)  # (3)! 
    is_active: bool = True
```

1. Same as `conint(ge=0)`
2. Same as `constr(pattern=r'^\w+$')`
3. Same as `conint(ge=14)`

Here setting the default value of age can be achieved in only one way.

```python
age: int = Field(18, ge=14)
```

/// info
If you use **Field Types** simultaneously with **Constrained Types**, you should know about validation priority.

1. When using `Field` directly, **Constrained Type** takes precedence over `Field`.
    ```python
    username: constr(min_length=5) = Field(min_length=10)
    ```   

2. When use `Field` + `Annotated`, `Field` take precedence over **Constrained Type**.
    ```python 
    username: Annotated[constr(min_length=5), Field(min_length=10)]
    ```
///

#### Validators

In addition to using Constrained Types and Fields for validation,
you can also define custom validation logic in your model using validators.
Validators allow you to apply more complex validation rules that cannot be easily expressed using the built-in
types or field constraints.

Here's an example of how you can validate the email field:

```python
import re
from sensei import APIModel
from typing import Annotated
from pydantic import Field, field_validator


class User(APIModel):
    id: Annotated[int, Field(ge=0)]
    username: Annotated[str, Field(pattern=r'^\w+$')]
    email: str
    age: Annotated[int, Field(18, ge=14)]
    is_active: bool = True

    @field_validator('email')
    def validate_email(cls, value):
        pattern = r'^[\w\.-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, value):
            raise ValueError(f"Email '{value}' does not match the required pattern.")

        return value
```

Validator is defined through the `@field_validator` decorator from `pydantic`.
You can pass one or more field names to `@field_validator`, to determine what fields will use this validator, or `'*'`
to apply
validator for every field. The decorator is applied to a class method,
which takes the value of a field as an argument and returns the validated (or transformed) value. This method can also
raise a `ValueError` or `TypeError` to signal a validation failure.

/// tip
In situations, when you use `@field_validator` along with other validators, like built-in `Field`, you may need to
set the execution order of your custom validator. There is `mode` argument, to customize it.

- `mode="before"` - validator is executed before the `pydantic` internal parsing.
- `mode="after"` - validator is executed after the `pydantic` internal parsing.
- `mode="plain"` - validator terminates other validators, no further validators are called
- `mode="wrap"` - validator can run code before the `pydantic` internal parsing and after.

Here is an example of how to use comma-separated tags, in result will be represented as `list[str]`

```python
from sensei import APIModel
from typing import Annotated
from pydantic import Field, field_validator


class Video(APIModel):
    tags: Annotated[list[str], Field(min_length=1)]
    ...

    @field_validator('tags', mode="before")
    def _split_str(cls, value):
        if isinstance(value, str):
            return value.split(',')
        else:
            return value


print(Video(tags='trend,unreal,good'))
```

```python
Video(tags=['trend', 'unreal', 'good'])
```

///

### Serializing

To serialize a model, you can use the `model_dump` method.

```python
user = User(id=1, username="johndoe", email="johndoe@example.com", age=30)
user_data = user.model_dump(mode="json")
print(user_data)
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
If you use a model in another request or want to write it to a file, you should serialize it with `mode="json"`.

```python
user_data = user.model_dump(mode="json")
```

For example, if you have some field with `datetime` object, this mode evaluates this time as a string.

```python
from sensei import APIModel
from datetime import datetime


class Task(APIModel):
    due_date: datetime
    ...


task = Task(due_date=datetime(2024, 10, 15, 15, 30)).model_dump(mode="json")
print(task)
```
```json
{
  "date": '2024-10-15T15:30:00',
  ...
}
```
///

### Routed Methods

You can create a model that performs both validation and making requests. This OOP Style is called [Routed Model](/learn/user_guide/routed_model.html)
(we will explore it later).

```python
from typing import Annotated
from typing_extensions import Self
from sensei import APIModel, Router, Path
from pydantic import NonNegativeInt, EmailStr

router = Router('https://api.example.com/')

class User(APIModel):
    id: NonNegativeInt
    username: str
    email: EmailStr
    
    @classmethod
    @router.get('/users/{id_}')
    def get(cls, id_: Annotated[NonNegativeInt, Path()]) -> Self: 
        pass # (1)!
```

1. This is called [routed method](/learn/user_guide/first_steps.html#routed-function)

The algorithm is the following:

1. Create a `Router` instance
    ```python
    router = Router('https://api.example.com/')
    ```

2. Define endpoints through [routed methods](/learn/user_guide/first_steps.html#routed-function)
    ```python
    @classmethod
    @router.get('/users/{id_}')
    def get(cls, id_: Annotated[NonNegativeInt, Path()]) -> Self: 
        pass 
    ```    

As a result, `User.get` returns `User` object:

```python
user = User.get(1)
print(user.email)
```

```text
george.bluth@gmail.com
```

[Routed Model](/learn/user_guide/routed_model.html) is a good practice to organize endpoints in one class when they are related to one model.

/// warning
You must not decorate a method as routed in a class not inherited from `APIModel`.
This makes it impossible to use [Preparers/Finalizers](/learn/user_guide/preparers_finalizers.html), which we will learn in 
the future, and can lead to issues in the other situations.

For instance, there is a common error to use `BaseModel` for the same purpose as `APIModel`:

```python
from pydantic import BaseModel
from typing import Annotated
from typing_extensions import Self
from sensei import Router, Path
from pydantic import NonNegativeInt

router = Router('https://api.example.com/')

class User(BaseModel):
    @classmethod
    @router.get('/users/{id_}')
    def get(cls, id_: Annotated[NonNegativeInt, Path()]) -> Self: 
        pass 
```

///

## Recap

Sensei abstracts away much of the manual work, letting developers focus on function signatures while the framework
handles the API logic and data validation.

The example of [First Request](#first-request) demonstrates a simple and robust HTTP request using the Sensei framework.
Here's the key breakdown of the process:

### 1. Importing Dependencies:

- `Router` manages API endpoints and routing.
- `Path` specifies and validates route parameters.
- `APIModel` defines models for structuring API responses (similar to `pydantic.BaseModel`).

### 2. Creating the Router:

The `Router` is initialized with the base URL of the *PokéAPI*. All subsequent requests will use this as the base path.

### 3. Defining the Model:

The `Pokemon` class represents the data structure for a Pokémon, with fields like `name`, `id`, `height`, and `weight`.
It inherits from `APIModel`, which provides validation and serialization.

### 4. Creating the Endpoint:

The `get_pokemon` function is a [routed function](/learn/user_guide/first_steps.html#routed-function)
decorated with `@router.get`, defining a GET request for`/pokemon/{name}`.
This uses `Annotated` to ensure that `name` is a string and adheres to the validation rule (max length of 300).

### 5. Making the Request:

By calling `get_pokemon(name="pikachu")`, Sensei automatically handles validation, makes the HTTP request,
and maps the API response into the `Pokemon` model. The code omits the function body since Sensei handles calls through
the function's signature.