## Param Types

**Param Types** is the set of objects to declare request parameter of a specific type through type hints,
There are `Path`, `Query`, `Cookie`,`Header`, `Body`, `File`, `Form`.

/// tip
If you don't know the types of "request parameters", visit [HTTP Requests](/learn/http_requests.html){.internal-link}
///

Sensei's Param Types are inherited from `FieldInfo`, produced by the `Field` function. You can apply the same approaches
that was described for [Field Types](/learn/user_guide/first_steps.html#field-types){.internal-link}.

??? example
    Here is a function that creates a user and returns a JWT token, corresponding to the user.
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
    pass
```

When using the `Path` parameter, a placeholder name must match the argument name.

/// tip
If you are sure that you will not write validations, you can omit the `Path` declaration.

```python
@router.get('/posts/{id_}')
def get_post(cls, id_: int) -> Post:
    pass
```

///

### Query

This uses a query parameter to search for users based on a string.

```python
@router.get('/search')
def search_users(cls, query: Annotated[str, Query()] = "") -> list[User]:
    pass
```

/// tip
If you use a method, that usually includes query parameters, you can omit the `Query` declaration.

```python
@router.get('/search')
def search_users(cls, query: str = "") -> list[User]:
    pass
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
    pass
```

`Body` parameters have arguments that other parameters don't have:

#### MIME-type

If the content of your request body is not default (e.g JSON), you can change its media type:

!!! example
    ```python
    @router.post('/create_user')
    def create_user(cls, user: Annotated[User, Body(media_type='application/xml')]) -> User:
        pass
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
    pass
```

This will produce the following request:

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
    pass
```

This will produce the following request:

```json
{
  "name": "John Doe",
  "email": "john.doe@example.com"
}
```

Here, the body directly contains the serialized `User` object.

/// tip
If you use a method, that usually includes the request body, you can omit the `Body` declaration.

```python
@router.post('/create_user')
def create_user(cls, user: User) -> User:
    pass
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
    pass
```

/// note | Technical Details
`Form` is inherited from `Body`. You can use the `embed` argument, but can't use `media_type`, because `Form` has preset
`media_type='application/x-www-form-urlencoded'`.
You can achieve the same functionality if use `Body(media_type='application/x-www-form-urlencoded')` instead of `Form`.
///

### File

This accepts an image file from the request as a `File`.

```python
@router.post('/upload')
def upload_image(cls, image: Annotated[bytes, File()]) -> str:
    pass
```

`File` is inherited from `Form`, consequently there is `embed` argument like in `Body`.

/// warning
Despite `File` being inherited from `Form`, which is inherited from `Body`, you cannot achieve the same functionality,
if using `Body(media_type='multipart/form-data')` instead of `File`. It's because `File` parameters are serialized differently.

Let's assume you use `Body(media_type='multipart/form-data')` instead of `File`. If you try to pass the content of binary
file with non-UTF8 characters, Sensei cannot finish serialization and will throw the `UnicodeDecodeError`.

??? failure "UnicodeDecodeError"
    ```python 
    @router.post('/upload')
    def upload_image(image: Annotated[bytes, Body(media_type='multipart/form-data')]) -> str:
        pass

    with open('/path/to/image', 'rb') as f:
        image = f.read()
    
    print(upload_image(image)) # <--- UnicodeDecodeError
    ```
    'utf-8' codec can't decode byte 0x89 in position 0: invalid utf-8

///

### Header

This function downloads a file while authenticating the user with a token from the headers:

```python
@router.get('/download')
def download_file(cls, x_token: Annotated[str, Header()]) -> bytes:
    pass
```

/// info
When your endpoint relies on custom headers, that are not supported by default in HTTP, you should call it with the prefix `X-`.
For instance, we want to define a header containing the request signature, that is encoded metadata, such as current time, 
your username, etc. You should call it like this:

```text
X-Signature
```
///

### Cookie:

This requires `session_id` from the browser cookies for user verification.

```python
@router.get('/verify')
def verify_user(cls, session_id: Annotated[str, Cookie()]) -> bool:
    pass
```

## Response Types

Response type is the return type of [routed function(method)](first_steps.md#routed-function){.internal-link}. 
There is a category of response types, that doesn't require [Preparers/Finalizers](/learn/user_guide/preparers_finalizers.html){.internal-link}, 
that we will learn in the future. That means these types are handled automatically. This category includes:

### `None`

If this type is present or a function has no return type, `None` is returned.

!!! example
    You can use `None` when a function doesn't return a relevant response or doesn't return it at all. 
    For instance, endpoints with the `DELETE` method often don't return the response.

    ```python
    @router.delete('/users')
    def delete_user() -> None: 
        pass
    ```

### `str`

`str` response type refers to the text representation of the response. If this type is present, the `text` attribute
of the `Response` object is returned.

!!! example
    When you need to get the `html` code of a page, you can use `str`.

    ```python
    @router.get('/index.html')
    def get_page() -> str: 
        pass

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
        <a href="https://example.com">Visit</a>
    </body>
    </html>
    ```

### `bytes`

`bytes` response type refers to the raw binary representation of the response. If this type is present, the `content`
attribute
of the `Response` object is returned.

!!! example
    When you need to query the binary file, you can use `bytes`.

    ```python
    from PIL import Image
    from io import BytesIO

    @router.get('/ai_image')
    def generate_image(style: str, resolution: Resolution) -> bytes: 
        pass
    
    image_bytes = generate_image("cartoon", Resolution(1200, 400))
    image = Image.open(BytesIO(image_bytes))
    ```

### `dict`

`dict` response type refers to the JSON representation of the response. 
In particular, it refers to JSON as a `dict`. Don't confuse with [`list[dict]`](/learn/user_guide/params_response.html#listdict){.internal-link}. 

If this type is present and the method is not OPTIONS or HEAD, the result of the `json()` method of the `Response` object is returned.
Otherwise, if the method is OPTIONS or HEAD, the attribute `headers` of the `Response` object is returned. This is the only response
type that can be used for automatic header extraction.

Instead of `dict` you can provide `dict[KT, VT]`, where `KT` is the key type and `VT` is the value type.

/// tip
Use the `dict` response type only when you want to get headers,
using 'HEAD' or 'OPTIONS' method, or response validation is redundant or useless
      
In this example, adding validations for the `version` and `available` fields could be redundant. Especially, if this function
is used as a helper.

```python
@router.get('/status')
def get_status() -> dict[str, Union[str, bool]]: pass

get_status()
```

```json
{
  "version": "1.0.0",
  "available": true
}

```

Or if this endpoint provides useful headers, we can get it using the `dict` response type.
```python
@router.head('/status')
def get_status() -> dict[str, Any]: pass

get_status()
```

///

### `list[dict]`

`list[dict]` response type also refers to the JSON representation of the response, but it refers to JSON as a `list[dict]`. 
If this type is present, the result of the `json()` method of the `Response` object is returned.

Instead of `list[dict]` you can provide `list[dict[KT, VT]]`, where `KT` is the key type and `VT` is the value type.

/// tip
Most probably, you will not find a situation, where JSON is represented as a `list`. 
But a list can be wrapped in a field, such as "data". 
You can use this type in combination with `__finalize_json__` hook, that we will cover in 
[Preparers/Finalizers](/learn/user_guide/preparers_finalizers.html){.internal-link}. 

This response type also should be used when response validation is redundant or useless.
   
In this example, if we need this model only as output in this function and don't need the same model as input in others, 
you can use `list[dict]`

```python
@router.get('/users')
def get_users() -> list[dict[str, Union[str, int]]]: 
    pass
```
///

### `<BaseModel>`
`<BaseModel>` response type refers to unpacking JSON representation of the response to the constructor of a 
subclass of `pydantic.BaseModel`. This means: 

1) If the response is represented as a dictionary, like that:
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

3) And unpack `{"name":  "alex", "id":  1, "city":  "Manchester"}` to `User`. As a result, you will have a `User` object. 
       ```python
       User(id=1, name='alex', city='Manchester')
       ```

The algorithm above is what Sensei does when you provide a `<BaseModel>` response type. 
                            
/// info
Here `<BaseModel>` is a placeholder, that should be substituted by the class name of the model, inherited from `BaseModel`.  
///        

This response type is better than `dict` because validations of `BaseModel` are
performed. But unlike `dict`, this type can't be used for automatic header extraction.


!!! example
    Here is example was shown in [First Steps](/learn/user_guide/first_steps.html#first-request){.internal-link}
    ```python
    class Pokemon(APIModel):
        name: str
        id: int
        height: int
        weight: int
    
    @router.get('/pokemon/{name}')
    def get_pokemon(name: Annotated[str, Path(max_length=300)]) -> Pokemon: 
        pass
    ```

### `list[<BaseModel>]`
`list[BaseModel]` response type refers to **sequential** unpacking JSON representation of the response to the constructor of a 
subclass of `pydantic.BaseModel`. That means: 

1) If response is represented as a list of dictionaries of the same structure, like that:  
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
       to `User`, etc. As a result, you will have a list of `User` objects. 
       ```python
       [User(id=1, name='alex', city='Manchester'), User(id=2, name='bob', city='London'), ...]
       ```

The algorithm above is what Sensei does when you provide a `list[<BaseModel>]` response type.


/// info
Here `<BaseModel>` is a placeholder, that should be substituted by the class name of the model, inherited from `BaseModel`.  
///  

This response type is better than `list[dict]`, because validations of `BaseModel` are
performed.
       
/// tip
Most probably, you will not find a situation, where JSON is represented as a `list`. 
But a list can be wrapped in a field, such as "data". 
You can use this type in combination with `__finalize_json__` hook, that we will cover in 
[Preparers/Finalizers](/learn/user_guide/preparers_finalizers.html){.internal-link}.

```python
@router.get('/users')
def get_users() -> list[User]: 
    pass
```
///

### `Self`
`Self` response type is used only in [routed methods](/learn/user_guide/first_steps.html#routed-methods){.internal-link}, 
specifically in class method (`@classmethod`) and instance methods (`self`). 
To use `Self`, you need to import it.
          
In python 3.9
```python
from typing_extensions import Self
```

In python >=3.10
```python
from typing import Self
```

Let's explore two use cases:

#### Class Method
`Self` in class method refers to the same as [`<BaseModel>`](/learn/user_guide/params_response.html#basemodel){.internal-link}. 
The current class in which the method is declared is taken as the model.
    
!!! example
    ```python
    class User(APIModel):
        @classmethod
        @router.get('/users/{id_}')
        def get(cls, id_: Annotated[NonNegativeInt, Path()]) -> Self: 
            pass
    ```

#### Instance Method
`Self` in instance method refers to the current object from which the method was called. This object is returned.

!!! example
    You can use it in `PUT` and `PATCH` methods that update data related to the current model. It's a common approach, 
    to return the object for which the update was called.

    In this example, we use [Preparers/Finalizers](/learn/user_guide/preparers_finalizers.html){.internal-link} 

    ```python
    class User(APIModel):
        ...
        @router.patch('/users/{id_}')
        def update(
                self,
                name: str,
                job: str
        ) -> Self:
            pass
    
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
In Python 3.9 `Self` is not included in the `typing` module, but is included in `typing_extensions`. 
Because of this, IDEs often cannot understand this return type in Python 3.9. 
You can achieve the same functionality using **Forward References**.

/// info
[Forward reference](https://peps.python.org/pep-0484/#forward-references){.external-link} is a way to resolve the issue, when a type hint contains names that have not been defined yet. 
It is a string literal, that can express a definition, to be resolved later. 

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
class User(APIModel):
    ...
    @classmethod
    @router.get('/users/{id_}')
    def get(cls, id_: Annotated[NonNegativeInt, Path()]) -> Self: 
        pass
```

Can also be written as:

```python
class User(APIModel):
    ...
    @classmethod
    @router.get('/users/{id_}')
    def get(cls, id_: Annotated[NonNegativeInt, Path()]) -> "User": 
        pass
```

/// warning
Forward Reference can only be used in routed methods (not routed functions). In the following example, Sensei cannot 
understand the response type.

```python
class User(APIModel):
    email: EmailStr
    id: PositiveInt
    first_name: str
    last_name: str
    avatar: AnyHttpUrl

@router.get('/users')
def list(
        cls,
        page: Annotated[int, Query()] = 1,
        per_page: Annotated[int, Query(le=7)] = 3
) -> list["User"]:
    pass

@router.get('/users/{id_}')
def get(cls, id_: Annotated[int, Path(alias='id')]) -> "User": 
    pass
```


///
         
### `list[Self]`
`list[Self]` it's a mix of [`list[<BaseModel>]`](/learn/user_guide/params_response.html#listbasemodel){.internal-link} 
and [`Self`](/learn/user_guide/params_response.html#self){.internal-link}. It refers to **sequential** unpacking JSON representation 
of the response to the constructor of a current `BaseModel` class from which the method was called. 
But unlike `Self`, it can be used only in class methods.

You can use [Forward References](/learn/user_guide/params_response.html#forward-reference){.internal-link} as well as for 
`Self`

!!! example
    This code 
    ```python
    @router.get('/users')
    def get_users() -> list[User]: 
        pass
    ```

    Can be rewritten as
    ```python
    class User(APIModel)
        ...
        @router.get('/users')
        def list() -> list[Self]: 
            pass
    ```    

    Or as
    ```python
    class User(APIModel)
        ...
        @router.get('/users')
        def list() -> list["User"]: 
            pass
    ```
     
## Recap

In Sensei, defining [Param Types](#param-types){.internal-link} and [Response Types](#response-types){.internal-link} enables structured request and response handling, 
promoting flexibility, code clarity, and effective validation. Here's a brief overview:

1. **Param Types** are used to specify the origin of parameters in HTTP requests (`Path`, `Query`, `Cookie`, `Header`, 
     `Body`, `File`, `Form`). They provide a consistent way to validate requests:
     - `Path` is for URL path params, `Query` is for URL queries, and `Body` is for JSON data in requests.
     - `File` and `Form` types cater to form data, with `File` designed for binary files.
     - `Header` and `Cookie` handle HTTP headers and cookies, respectively.

2. **Response Types** define the structure of responses and support automated JSON parsing and response validation:
     - Basic types like `str`, `bytes`, `None`, and `dict` provide flexible output for text, binary data, or basic JSON.
     - Structured response types using `BaseModel` ensure data validation, with `Self` and `list[Self]` enhancing 
       functionality in OOP-style.
   
Using these types, Sensei promotes readability and robustness in handling HTTP request/response patterns. 
Additionally, automated validations streamline error handling, while options like `Self` and `list[Self]` 
provide scalability for complex models and responses, keeping code DRY and maintainable.