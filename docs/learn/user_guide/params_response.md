## Param Types

**Param Types** is set of objects to declare request parameter of a specific type through type hints,
There are `Path`, `Query`, `Cookie`,`Header`, `Body`, `File`, `Form`.

/// tip
If you don't know types of "request parameters", visit [HTTP Requests](/learn/http_requests.html)
///

Sensei's Param Types are inherited from `FieldInfo`, produced by `Field` function. You can apply the same approaches
that was described for [Field Types](/learn/user_guide/first_steps.html#field-types).

!!! example
    Here is a function that creates user and returns JWT token, corresponding to the user.
    ```python
    @router.post('/users')
    def create_user(
        id: Annotated[int, Body(ge=0)],
        username: Annotated[str, Body(pattern=r'^\w+$')],
        email: Annotated[EmailStr, Body()],
        age: Annotated[int, Body(ge=14)] = 18,
        is_active: Annotated[bool, Body()] = True,
    ) -> str:
       pass
    ```

Let's create some models and show examples, using them.

```python
class User:
    email: EmailStr
    id: PositiveInt
    first_name: str
    last_name: str
    avatar: AnyHttpUrl


class Post:
    id: PositiveInt
    title: str
    content: str
    created_at: datetime.datetime
```

### Path

This endpoint retrieves a post by its ID from the URL path.

```python
@router.get('/posts/{id_}')
def get_post(cls, id_: Annotated[int, Path()]) -> Post:
    ...
```

When use `Path` parameter, placeholder name must match argument name.

/// tip
If you are sure that you will not write validations, you can omit `Path` declaration.

```python
@router.get('/posts/{id_}')
def get_post(cls, id_: int) -> Post:
    ...
```

///

### Query

This uses a query parameter to search for users based on a string.

```python
@router.get('/search')
def search_users(cls, query: Annotated[str, Query()] = "") -> list[User]:
    ...
```

/// tip
If you use method, that usually include query parameters, you can omit `Query` declaration.

```python
@router.get('/search')
def search_users(cls, query: str = "") -> list[User]:
    ...
```

Methods that usually include query parameters:

- GET
- DELETE
- HEAD
- OPTIONS
///

### Body

This accepts a `User` object in the request body for user creation.

```python
@router.post('/create_user')
def create_user(cls, user: Annotated[User, Body()]) -> User:
    ...
```

`Body` parameters have arguments that other parameters don't have:

#### MIME type

If the content of your request body is not default (e.g JSON), you can change its media-type

!!! example
    ```python
    @router.post('/create_user')
    def create_user(cls, user: Annotated[User, Body(media_type='application/xml')]) -> User:
        ...
    ```

#### Embed/Non-embed

The `embed` parameter in Sensei's `Body()` function determines how the request body should be formatted when passed.
When `embed` is set to `True` (which is the default), the request body expects the object to be wrapped inside a
dictionary with a specific key.
When `embed` is set to `False`, the object itself is expected to be the body of the request
without being wrapped in a dictionary.

Here are examples of both scenarios:

##### Embed (default)

When `embed=True` (default), the `User`  is wrapped inside a key (e.g., "user"), so the body needs to provide a
key-value pair where the value is the actual `User`.

```python
@router.post('/create_user')
def create_user(user: Annotated[User, Body(embed=True)]) -> User:
    ...
```

This will produce the following request

```json
{
  "user": {
    "name": "John Doe",
    "email": "john.doe@example.com"
  }
}
```

In this case, the body contains a dictionary with the key `"user"`, and the value is the serialized `User` object.

##### Non-embed

When `embed=False`, the `User` is expected to be the body itself, like this:

```python
@router.post('/create_user')
def create_user(user: Annotated[User, Body(embed=False)]) -> User:
    ...
```

This will produce the following request

```json
{
  "name": "John Doe",
  "email": "john.doe@example.com"
}
```

Here, the body directly contains the serialized `User` object.

/// tip
If you use method, that usually include request body, you can omit `Body` declaration.

```python
@router.post('/create_user')
def create_user(cls, user: User) -> User:
    ...
```

Methods that usually include request body:

- POST
- PUT
- PATCH
///

### Form

Here, `username` and `password` are captured from a form submission.

```python
@router.post('/login')
def login_user(cls, username: Annotated[str, Form()], password: Annotated[str, Form()]) -> str:
    ...
```

/// note | Technical Details
`Form` is inherited from `Body`. You can use `embed` argument, but can't use `media_type`, because `Form` has preset
`media_type='application/x-www-form-urlencoded'`.
You can achive the same functionality, if use `Body(media_type='application/x-www-form-urlencoded')` instead of `Form`.
///

### File

This accepts an image file from the request as a `File`.

```python
@router.post('/upload')
def upload_image(cls, image: Annotated[bytes, File()]) -> str:
    ...
```

`File` is inherited from `Form`, consequently there is `embed` argument like in `Body`.

/// warning
Despite `File` is inherited from `Form`, which is inherited from `Body`, you cannot achieve the same functionality,
if use `Body(media_type='multipart/form-data')` instead of `File`. It's because `File` parameters are serialized in
a different way.

Let's assume you use `Body(media_type='multipart/form-data')` instead of `File`. If you try to pass content of binary
file with non-UTF8 characters, Sensei cannot finish serialization and will throw the `UnicodeDecodeError`.

!!! failure "UnicodeDecodeError"
    ```python 
    @router.post('/upload')
    def upload_image(image: Annotated[bytes, Body(media_type='multipart/form-data')]) -> str:
        ...

    with open('/path/to/image', 'rb') as f:
        image = f.read()
    
    print(upload_image(image)) # <--- UnicodeDecodeError
    ```
    'utf-8' codec can't decode byte 0x89 in position 0: invalid utf-8

///

### Header

This function downloads a file while authenticating the user with a token from headers

```python
@router.get('/download')
def download_file(cls, auth_token: Annotated[str, Header()]) -> bytes:
    ...
```

### Cookie:

This requires `session_id` from the browser cookies for user verification.

```python
@router.get('/verify')
def verify_user(cls, session_id: Annotated[str, Cookie()]) -> bool:
    ...
```

## Response Types

Response type is the return type of routed function(method). There is a category of response types, that doesn't require
[Preparers/Finalizers](/learn/user_guide/preparers_finalizers.html), that we will learn in the future.
That means these types are handled automatically. This category includes:
        
### `None`

If this type is present or function has no return type , `None` is returned.

!!! example
    You can use `None`, when function doesn't return relevant response or doesn't return it at all. 
    For instance, endpoints with `DELETE` method often don't return a response.

    ```python
    @router.delete('/users')
    def delete_user() -> None: ...
    ```

### `str`

`str` response type refers to the text representation of a response. If this type is present, the `text` attribute
of `Response` object is returned.

!!! example
    When you need to get `html` code of a page, you can use `str`.

    ```python
    @router.get('/index.html')
    def get_page() -> str: ...

    get_page()
    ```

    ```html
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Main page</title>
    </head>
    <body>
        <h1>Hello, World!</h1>
        <a href="https://example.com">Visite</a>
    </body>
    </html>
    ```

### `bytes`

`bytes` response types refers to raw binary representation of a response. If this type is present, the `content`
attribute
of `Response` object is returned.

!!! example
    When you need to query the binary file, you can use `bytes`.

    ```python
    from PIL import Image
    from io import BytesIO

    @router.get('/ai_image')
    def generate_image(style: str, resolution: Resolution) -> bytes: ...
    
    image_bytes = generate_image("cartoon", Resolution(1200, 400))
    image = Image.open(BytesIO(image_bytes))
    ```

### `dict`

`dict` response type refers to the JSON representation of a response. 
In particular, it refers to JSON as a `dict`. Don't confuse with [`list[dict]`](/learn/user_guide/params_response.html#listdict). 
If this type is present, the result of `json()` method of `Response` object is returned.

Instead of `dict` you can provide `dict[KT, VT]`, where `KT` is key type and `VT` is value type.

/// tip
Use `dict` response type only when response validation is redundant or useless
      
In this example, adding validations for `version` and `available` field could be redundant. Especially, if this function
is used as helper.

```python
@router.get('/status')
def get_status() -> dict[str, Union[str, bool]]: ...


get_status()
```

```json
{
  "version": "1.0.0",
  "available": true
}
```

///

### `list[dict]`

`list[dict]` response type also refers to the JSON representation of a response, but it refers to JSON as a `list[dict]`. 
If this type is present, the result of `json()` method of `Response` object is returned.

Instead of `list[dict]` you can provide `list[dict[KT, VT]]`, where `KT` is key type and `VT` is value type.

/// tip
Most probably, you will not find a situation, where JSON is represented as `list`. 
But a list can be wrapped in a field, such as "data". 
You can use this type in combination with `__finalize_json__` hook, that we will cover in 
[Preparers/Finalizers](/learn/user_guide/preparers_finalizers.html). 

This response type also should be used when response validation is redundant or useless.
   
In this example, if we need this model only as output in this function and don't need the same model as input in other, 
you can use `list[dict]`

```python
@router.get('/users')
def get_users() -> list[dict[str, Union[str, int]]]: ...
```
///

### `<BaseModel>`
`<BaseModel>` response type refers to unpacking JSON representation of a response to the constructor of a 
subclass of `BaseModel` from `pydantic`. This means: 

1) If response is represented as a dictionary, like that:
        ```json
        {"name":  "alex", "id":  1, "city":  "Manchester"}
        ```

2) You can make this model:
       ```python
       class User(APIModel):
           id: NonNegativeInt
           name: str
           city: str
       ```

3) And unpack `{"name":  "alex", "id":  1, "city":  "Manchester"}` to `User`. As a result you will have `User` object. 
       ```python
       User(id=1, name='alex', city='Manchester')
       ```

The algorithm above is what Sensei does, when you provide `<BaseModel>` response type. 
                            
/// info
Here `<BaseModel>` is a placeholder, that should be substituted by class name of model, inherited from `BaseModel`.  
///        

This response type is better than `dict`, because validations of `BaseModel` are
performed.


!!! example
    Here is example was shown in [First Steps](/learn/user_guide/first_steps.html#first-request)
    ```python
    class Pokemon(APIModel):
        name: str
        id: int
        height: int
        weight: int
    
    @router.get('/pokemon/{name}')
    def get_pokemon(name: Annotated[str, Path(max_length=300)]) -> Pokemon: 
        ...
    ```

### `list[<BaseModel>]`
`list[BaseModel]` response type refers to **sequential** unpacking JSON representation of a response to the constructor of a 
subclass of `BaseModel` from `pydantic`. That means: 

1) If response represented as a list of dictionaries of the same structure, like that:  
        ```json
        [{"name":  "alex", "id":  1, "city":  "Manchester"}, {"name":  "bob", "id":  2, "city":  "London"}, ...]
        ```
           
2) You can make this model:
        ```python
        class User(APIModel):
            id: NonNegativeInt
            name: str
            city: str
        ```

3) And unpack `{"name":  "alex", "id":  1, "city":  "Manchester"}` to `User`, `{"name":  "bob", "id":  2, "city":  "London"}`
       to `User`, etc. As a result you will have list of `User` objects. 
       ```python
       [User(id=1, name='alex', city='Manchester'), User(id=2, name='bob', city='London'), ...]
       ```

The algorithm above is what Sensei returns, when you provide `list[<BaseModel>]` response type.


/// info
Here `<BaseModel>` is a placeholder, that should be substituted by class name of model, inherited from `BaseModel`.  
///  

This response type is better than `list[dict]`, because validations of `BaseModel` are
performed.
       
/// tip
Most probably, you will not find a situation, where JSON is represented as `list`. 
But a list can be wrapped in a field, such as "data". 
You can use this type in combination with `__finalize_json__` hook, that we will cover in 
[Preparers/Finalizers](/learn/user_guide/preparers_finalizers.html).

```python
@router.get('/users')
def get_users() -> list[User]: ...
```
///

### `Self`
`Self` response type is used only in, but it's used only in [routed methods](/learn/user_guide/first_steps.html#routed-methods)
of classes (see `OOP-style`), specifically in class method(`@classmethod`) and instance methods(`self`). To use `Self`, 
you need to import it.
          
In python 3.8
```python
from typing_extensions import Self
```

In python >=3.9
```python
from typing import Self
```

Let's explain two use cases:

#### Class Method
`Self` in class method refers to the same as [`<BaseModel>`](/learn/user_guide/params_response.html#basemodel). 
The current class in which the method is declared is taken as the model
    
!!! example
    ```python
    @router.model()  
    class User(APIModel):
        @classmethod
        @router.get('/users/{id_}')
        def get(cls, id_: Annotated[NonNegativeInt, Path()]) -> Self: 
            ...
    ```

#### Instance Method
`Self` in instance method refers to the current object from which the method was called. This object is returned.

!!! example
    You can use it in `PUT` and `PATCH` methods that update data related to the current model. It's a common approach, 
    to return the object for which the update was called.

    In this example we use [Preparers/Finalizers](/learn/user_guide/preparers_finalizers.html) 

    ```python
    class User(APIModel):
        ...
        @router.patch('/users/{id_}')
        def update(
                self,
                name: str,
                job: str
        ) -> Self:
            ...
    
        @update.prepare
        def _update_in(self, args: Args) -> Args:
            args.url = format_str(args.url, {'id_': self.id})
            return args
    
        @update.finalize()
        def _update_out(self, response: Response) -> Self:
            json_ = response.json()
            self.first_name = json_['name']
            return self
    ```

#### Forward Reference
In python 3.8 `Self` is not included into `typing` module, but is included into `typing_extensions`. If for some reason you can't use `Self`, you can achieve
the same functionality using **Forward References**.

/// info
[Forward reference](https://peps.python.org/pep-0484/#forward-references) is way to resolve issue, when a type hint contains names that have not been defined yet. 
Basically, it is a string literal, that can express definition, to be resolved later. 

For example, the following code, namely constructor definition, does not work:

```python
class Tree:
    def __init__(self, left: Tree, right: Tree):
        self.left = left
        self.right = right
```

To address this, we write:

```python
class Tree:
    def __init__(self, left: 'Tree', right: 'Tree'):
        self.left = left
        self.right = right
```
///
       
For instance, this code:

```python
@router.model()  
class User(APIModel):
    @classmethod
    @router.get('/users/{id_}')
    def get(cls, id_: Annotated[NonNegativeInt, Path()]) -> Self: 
        ...
```

Can also be written as:

```python
@router.model()  
class User(APIModel):
    @classmethod
    @router.get('/users/{id_}')
    def get(cls, id_: Annotated[NonNegativeInt, Path()]) -> "User": 
        ...
```
         
### `list[Self]`
`list[Self]` it's a mix of [`list[<BaseMode>]`](/learn/user_guide/params_response.html#listbasemodel) 
and [`Self`](/learn/user_guide/params_response.html#self). It refers to **sequential** unpacking JSON representation 
of a response to the constructor of a current `BaseModel` class from which the method was called. 
But unlike [`Self`](/learn/user_guide/params_response.html#self), it can be used only in class methods.

!!! example
    This code 
    ```python
    @router.get('/users')
    def get_users() -> list[User]: ...
    ```

    Can be rewritten as
    ```python
    class User(APIModel)
        @router.get('/users')
        def list() -> list[Self]: ...
    ```    

#### Forward References 
You can use [Forward References](/learn/user_guide/params_response.html#forward-reference) as well as for 
[`Self`](/learn/user_guide/params_response.html#self)
