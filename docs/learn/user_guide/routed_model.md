/// tip
If you don't know what are `Self`, `list[Self]` response types and 
[Forward Reference](/learn/user_guide/params_response.html#forward-reference), you should read 
[Params/Response](/learn/user_guide/params_response.html).
///

**Routed Model** is OOP style of making Sensei models, when a model performs both validation and making request.
To use this style, you need to implement model derived from `APIModel` and add inside routed methods.
                                       
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
        ... # (1)!
```

1. This is called [routed method](/learn/user_guide/first_steps.html#routed-function)

As was mentioned before, you apply can the same techniques as for `pydantic.BaseModel`. These key principles were 
described in [First Steps/API Model](/learn/user_guide/first_steps.html#api-model).

/// warning
You must not decorate a method as routed in a class not inherited from `APIModel`.
This makes impossible to use [Preparers/Finalizers](/learn/user_guide/preparers_finalizers.html) and 
[Class Hooks](#class-hooks)

For instance, there is a common error to use `BaseModel` for the same purpose as `APIModel`:

```python
from pydantic import BaseModel
from typing import Annotated
from typing_extensions import Self
from sensei import Router, Path
from pydantic import NonNegativeInt, EmailStr

router = Router('https://api.example.com/')

class User(BaseModel):
    id: NonNegativeInt
    username: str
    email: EmailStr
    
    @classmethod
    @router.get('/users/{id_}')
    def get(cls, id_: Annotated[NonNegativeInt, Path()]) -> Self: 
        ... 
```
///

## Class Hooks
"Apply class hook" means the same as "apply hook at routed model level." Hook names are the same as
names of python dunder methods (short for "double underscore"). That is, the name starts with "\_\_" and ends with "\_\_".
In other words hooks are called by pattern `<__hook_name__>`.

??? info
    Dunder methods (short for "double underscore") are special methods in Python that start and end with double 
    underscores, like `__init__`, `__str__`, `__add__`, etc. These methods are also known as "magic methods" and 
    enable Python classes to implement specific behaviors by defining certain functionalities that get triggered under 
    particular conditions.

    Some common dunder methods include:

    - `__init__(self, ...)`: The initializer or constructor, which runs when a new instance of a class is created.
    - `__str__(self)`: Called by `str()` and `print()` to provide a human-readable string representation of the object.
    - `__repr__(self)`: Called by `repr()` and used to provide a developer-friendly string representation, often useful for debugging.
    - `__add__(self, other)`: Defines behavior for the `+` operator.
    - `__len__(self)`: Allows the use of `len()` on an instance of the class.
    - `__getitem__(self, key)`: Allows indexing, like `obj[key]`.
    - `__call__(self, ...)`: Allows an instance to be called as a function, using parentheses `()`.
    - `__eq__(self, other)`: Defines behavior for the equality operator `==`.

    Dunder methods allow you to customize the behavior of instances, often making them behave like built-in types in Python. 
    For example, by implementing `__add__`, you can enable the `+` operator to add two instances of a class in a custom way.
                   
To define some hook, you need to create a method `<__hook_name__>` inside model.
These methods can be represented as `@classmethod` or `@staticmethod`, but not instance method.

!!! failure "ValueError"
    ```python
    class User(APIModel):
        email: str
        id: int
        first_name: str
        last_name: str
        avatar: str
    
        def __finalize_json__(self, json: Json) -> Json:
            print(super().__finalize_json__)
            return json['data']
        
        ...
    ```

    ValueError: Class hook \_\_finalize_json\_\_ cannot be instance method

### Case Converters
`<param_type>` corresponds to `__<param_type>_case__` hook. Let's look at the example below:

```python
router = Router(host, response_case=camel_case)

class User(APIModel):
    @classmethod
    def __header_case__(cls, s: str) -> str:
        return kebab_case(s)

    @staticmethod
    def __response_case__(s: str) -> str:
        return snake_case(s)

    @classmethod
    @router.get('/users/{id_}')
    def get(cls, id_: Annotated[int, Path(alias='id')]) -> Self: ...
```

As was mentioned before, hook function can be represented both as class method and as static method, but not instance methods.
   
/// tip
If you don't know why `response_case=camel_case` statement in `Router` constructor is ignored here, you should
read about [Priority Levels](/learn/user_guide/making_aliases.html#hook-levels-priority)             
///

### Preparers/Finalizers

Preparers

## Routed Methods

Routed Methods associated with the different routers

## Inheriting

Inheriting, to follow DRY