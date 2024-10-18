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

- **Fast:** Do not write any code-making request, dedicate responsibility to the function's interface(signature)
- **Short:** Avoid code duplication. 
- **Sync/Async:** Implement sync and async quickly, without headaches
- **Robust:** Auto validation data before and after request


## Quick Overview

API Wrapper should provide these features for users:

- Provide sync and async code versions
- Validate data before accessing the API.
- Handle RPS (Requests per second) limits.
- Return relevant response

And as a developer, you want to avoid code duplication and make routine things faster.

To follow all these principles, you either violate DRY or have to maintain bad code architecture. Sensei is a tool to avoid these issues.

Example code:

```python
import datetime
from typing import Annotated, Any, Self
from pydantic import EmailStr, PositiveInt, AnyHttpUrl
from sensei import Router, Query, Path, APIModel, Args, pascal_case, format_str, RateLimit
from httpx import Response

router = Router('https://reqres.in/api', rate_limit=RateLimit(5, 1))


@router.model()
class BaseModel(APIModel):
    def __finalize_json__(self, json: dict[str, Any]) -> dict[str, Any]:
        return json['data']

    def __prepare_args__(self, args: Args) -> Args:
        args.headers['X-Token'] = 'secret_token'
        return args

    def __header_case__(self, s: str) -> str:
        return pascal_case(s)


class User(BaseModel):
    email: EmailStr
    id: PositiveInt
    first_name: str
    last_name: str
    avatar: AnyHttpUrl

    @classmethod
    @router.get('/users')
    def list(
            cls,
            page: Annotated[int, Query()] = 1,
            per_page: Annotated[int, Query(le=7)] = 3
    ) -> list[Self]: # Framework knows how to handle response
        ...

    @classmethod
    @router.get('/users/{id_}')
    def get(cls, id_: Annotated[int, Path()]) -> Self: ...  # Framework knows how to handle response
    
    @router.patch('/users/{id_}', skip_finalizer=True)
    def update(
            self,
            name: str,
            job: str
    ) -> datetime.datetime:  # Framework does not know how to represent response as datetime object
        ...
    
    @update.prepare
    def _update_in(self, args: Args) -> Args:  # Get id from current object
        args.url = format_str(args.url, {'id_': self.id})
        return args
    
    @update.finalize()
    def _update_out(self, response: Response) -> datetime.datetime: # Specify hook, to handle response instead of framework
        json_ = response.json()
        result = datetime.datetime.strptime(json_['updated_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
        self.first_name = json_['name']
        return result

    @router.delete('/users/{id_}')
    def delete(self) -> Self: ...
    
    @delete.prepare
    def _delete_in(self, args: Args) -> Args:
        url = args.url
        url = format_str(url, {'id_': self.id})
        args.url = url
        return args

    @router.post('/token')
    def login(self) -> str: ...

    @login.prepare
    def _login_in(self, args: Args) -> Args:
        args.json_['email'] = self.email
        return args

    @login.finalize
    def _login_out(self, response: Response) -> str:
        return response.json()['token']

    @router.put('/users/{id_}', skip_finalizer=True)
    def change(
            self,
            name: Annotated[str, Query()],
            job: Annotated[str, Query()]
    ) -> bytes:
        ...

    @change.prepare
    def _change_in(self, args: Args) -> Args:
        args.url = format_str(args.url, {'id_': self.id})
        return args
```

As you can see, the functions` body have no code. You only need to describe the interface(signature) of the API endpoint, that is path, method, 
body and params, headers, and cookies, and specify its types and return(response) type. In most cases, the framework knows how to
handle a response to represent it as your return type, but when it cannot, you can use hooks to finalize the response or
prepare arguments for request. 

Example when the framework knows how to handle a response instead of you

```python
@classmethod
@router.get('/users')
def list(
        cls,
        page: Annotated[int, Query()] = 1,
        per_page: Annotated[int, Query(le=7)] = 3
) -> list[Self]: # Framework knows how to handle response
    ...
```
             
Example when you need to specify hook:

```python
@router.patch('/users/{id_}', skip_finalizer=True)
def update(
        self,
        name: str,
        job: str
) -> datetime.datetime:  # Framework does not know how to represent response as datetime object
    ...

@update.prepare
def _update_in(self, args: Args) -> Args:  # Get id from current object
    args.url = format_str(args.url, {'id_': self.id})
    return args

@update.finalize()
def _update_out(self, response: Response) -> datetime.datetime: # Specify hook, to handle response instead of framework
    json_ = response.json()
    result = datetime.datetime.strptime(json_['updated_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
    self.first_name = json_['name']
    return result
```

Let`s try to implement almost the same functionality, without using the framework!

```python
import httpx
import datetime
from typing import Any, Optional
from pydantic import BaseModel, EmailStr, PositiveInt, AnyHttpUrl, Field, ValidationError

TOKEN = 'secret_token'
BASE_URL =  'https://reqres.in/api' 

class User(BaseModel):
    email: EmailStr
    id: PositiveInt
    first_name: str
    last_name: str
    avatar: AnyHttpUrl

    @classmethod
    def _get_headers(cls) -> dict[str, str]:
        return {'X-Token': TOKEN}

    @classmethod
    def _handle_response(cls, response: httpx.Response) -> dict[str, Any]:
        response.raise_for_status()
        return response.json()

    @classmethod
    def _build_url(cls, endpoint: str) -> str:
        return f'{BASE_URL}{endpoint}'

    @classmethod
    def list(cls, page: Optional[int] = Field(1, ge=1), per_page: Optional[int] = Field(3, le=7)) -> list['User']:
        try:
            cls._validate_list_args(page, per_page)
        except ValidationError as e:
            raise ValueError(f"Invalid arguments: {e}")

        url = cls._build_url('/users')
        params = {'page': page, 'per_page': per_page}
        headers = cls._get_headers()

        response = httpx.get(url, params=params, headers=headers)
        data = cls._handle_response(response)['data']

        return [cls(**user_data) for user_data in data]

    @classmethod
    def _validate_list_args(cls, page: int, per_page: int) -> None:
        class ListArgs(BaseModel):
            page: int = Field(1, ge=1)
            per_page: int = Field(3, le=7)

        ListArgs(page=page, per_page=per_page)

    @classmethod
    def get(cls, id_: int) -> 'User':
        try:
            cls._validate_id(id_)
        except ValidationError as e:
            raise ValueError(f"Invalid ID: {e}")

        url = cls._build_url(f'/users/{id_}')
        headers = cls._get_headers()

        response = httpx.get(url, headers=headers)
        data = cls._handle_response(response)['data']

        return cls(**data)

    @classmethod
    def _validate_id(cls, id_: int) -> None:
        class IDModel(BaseModel):
            id_: PositiveInt

        IDModel(id_=id_)

    def update(self, name: str, job: str) -> datetime.datetime:
        try:
            self._validate_update_args(name, job)
        except ValidationError as e:
            raise ValueError(f"Invalid arguments: {e}")

        url = self._build_url(f'/users/{self.id}')
        headers = self._get_headers()
        json_data = {'name': name, 'job': job}

        response = httpx.patch(url, headers=headers, json=json_data)
        data = self._handle_response(response)

        self.first_name = data['name']
        return datetime.datetime.strptime(data['updated_at'], "%Y-%m-%dT%H:%M:%S.%fZ")

    def _validate_update_args(self, name: str, job: str) -> None:
        class UpdateArgs(BaseModel):
            name: str
            job: str

        UpdateArgs(name=name, job=job)

    def delete(self) -> 'User':
        url = self._build_url(f'/users/{self.id}')
        headers = self._get_headers()

        response = httpx.delete(url, headers=headers)
        self._handle_response(response)

        return self

    def login(self) -> str:
        try:
            self._validate_email(self.email)
        except ValidationError as e:
            raise ValueError(f"Invalid email: {e}")

        url = self._build_url('/token')
        headers = self._get_headers()
        json_data = {'email': self.email}

        response = httpx.post(url, headers=headers, json=json_data)
        return self._handle_response(response)['token']

    @classmethod
    def _validate_email(cls, email: str) -> None:
        class EmailModel(BaseModel):
            email: EmailStr

        EmailModel(email=email)

    def change(self, name: str, job: str) -> bytes:
        try:
            self._validate_update_args(name, job)
        except ValidationError as e:
            raise ValueError(f"Invalid arguments: {e}")

        url = self._build_url(f'/users/{self.id}')
        headers = self._get_headers()
        params = {'name': name, 'job': job}

        response = httpx.put(url, headers=headers, params=params)
        return response.content
```

This code is ~1.5 times bigger than the first and has no advantages over the code using the framework. He's just bigger. Some peoples would
suggest ideas to reduce duplication, but in big projects, these ideas lead to bad architecture, especially when you need to implement both
sync and async versions.

Also, you can handle API rate limiting, creating a `RateLimit` object.

```python
router = Router('https://reqres.in/api', rate_limit=RateLimit(5, 1))
```

Along with OOP, you can use functional style:

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

## Installing sensei
To install `sensei` from PyPi, you can use that:

```shell
pip install sensei
```

To install `sensei` from GitHub, use that:

```shell
pip install git+https://github.com/CrocoFactory/sensei.git
```