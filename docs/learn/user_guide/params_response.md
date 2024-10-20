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

Response Types
