If you are already motivated to use the framework, go to
[First steps](/learn/user_guide/first_steps.html)

## What is API Wrapper?

An API wrapper is a client-side collection of code that simplifies the interaction between a client application and a
web API.
The library abstracts the complexity of making HTTP requests, handling responses, and processing data, allowing
developers
to easily integrate API functionality without needing to deal with the lower-level details of the API's implementation.
Usually, you deal with API wrappers as Python libraries.

!!! example
`python-binance` library wrapping the API of the cryptocurrency exchange Binance.

      ```python
      from binance.client import Client
      
      client = Client(api_key='your_api_key', api_secret='your_api_secret')  # (1)!
      
      balance = client.get_asset_balance(asset='BTC')  # (2)!
      print(balance)
      
      prices = client.get_all_tickers()  # (3)!
      print(prices)
      
      order = client.order_market_buy(  # (4)!
         symbol='BTCUSDT',
         quantity=0.01
      )
      print(order)
      ```
      
      1. Create a client with API keys
      2. Get account balance information
      3. Get latest market prices
      4. Place a market buy order

## Golden Rules

Imagine you are one of the users using your API Wrapper.
Let's analyze the needs of the users.
We can list the most preferable features desired to be seen by the users:

### Sync and async code versions.

Since **User A** can create a CPU-bound application making few calls of functions from our
wrapper, he does not need to integrate app based on parallelism with three lines of async code.
Moreover, these lines will be evaluated only once per app session.
But **User B** can create an app that most of the time performs
I/O-bound work, consequently his concurrent application will benefit from these lines of async code.

But mostly it's hard to implement both versions of the code, following DRY principle.
Most of the attempts lead to the code duplication or bad code architecture.

///info
DRY (Don't Repeat Yourself) principle is a software development concept aimed at reducing the repetition of code and
logic.
The idea is that every piece of knowledge or logic should be represented in a single place in your codebase, and no
duplications
should exist. If you find yourself copying and pasting code, that’s a sign you’re violating DRY.
///

Let's show duplicated code example

#### Synchronous Example

```python
import httpx
from httpx import Response
from typing import Any


def validate_params(city: str, units: str) -> None:
    if not city:
        raise ValueError("City name cannot be empty")
    if units not in {"metric", "imperial"}:
        raise ValueError("Units must be 'metric' or 'imperial'")


def transform_response(response: Response) -> dict[str, Any]:
    data = response.json()
    return {
        "city": data["name"],
        "temperature": data["main"]["temp"],
        "description": data["weather"][0]["description"]
    }


def get_weather_sync(city: str, units: str = "metric") -> dict[str, Any]:
    validate_params(city, units)
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "units": units, "appid": "your_api_key"}
    headers = {"Accept": "application/json"}

    with httpx.Client() as client:
        response = client.get(url, params=params, headers=headers)
        return transform_response(response)


print(get_weather_sync("London"))
```

#### Asynchronous Example

```python
import httpx
import asyncio
from httpx import Response
from typing import Any


def validate_params(city: str, units: str) -> None:
    if not city:
        raise ValueError("City name cannot be empty")
    if units not in {"metric", "imperial"}:
        raise ValueError("Units must be 'metric' or 'imperial'")


def transform_response(response: Response) -> dict[str, Any]:
    data = response.json()
    return {
        "city": data["name"],
        "temperature": data["main"]["temp"],
        "description": data["weather"][0]["description"]
    }


async def get_weather_async(city: str, units: str = "metric") -> dict[str, Any]:
    validate_params(city, units)
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "units": units, "appid": "your_api_key"}
    headers = {"Accept": "application/json"}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, headers=headers)
        return transform_response(response)


async def main():
    print(await get_weather_async("London"))


asyncio.run(main())
```

#### Deduplicated version

Let's try to implement both versions and apply minimal duplication(deduplication), merging code into shared logic.

```python
import httpx
import asyncio
from httpx import Response, Client, AsyncClient
from typing import Any, Union

BaseClient = Union[Client, AsyncClient]
Components = tuple[str, dict[str, Any], dict[str, Any]]


def validate_params(city: str, units: str) -> None:  # (1)!
    if not city:
        raise ValueError("City name cannot be empty")
    if units not in {"metric", "imperial"}:
        raise ValueError("Units must be 'metric' or 'imperial'")


def transform_response(response: Response) -> dict[str, Any]:  # (2)!
    data = response.json()
    return {
        "city": data["name"],
        "temperature": data["main"]["temp"],
        "description": data["weather"][0]["description"]
    }


def build_request(
        client: BaseClient,
        url: str,
        params: dict,
        headers: dict
) -> Response:  # (3)!
    return client.get(url, params=params, headers=headers)


def get_components(city: str, units: str) -> Components:  # (4)!
    url = "https://api.openweathermap.org/data/2.5/weather"
    headers = {"Accept": "application/json"}
    params = {"q": city, "units": units, "appid": "your_api_key"}
    return url, headers, params


def get_weather_sync(city: str, units: str = "metric") -> dict[str, Any]:  # (5)!
    validate_params(city, units)

    url, headers, params = get_components(city, units)

    with httpx.Client() as client:
        response = build_request(client, url, params, headers)
        return transform_response(response)


async def get_weather_async(
        city: str,
        units: str = "metric"
) -> dict[str, Any]:  # (6)!
    validate_params(city, units)

    url, headers, params = get_components(city, units)

    async with httpx.AsyncClient() as client:
        response = await build_request(client, url, params, headers)
        return transform_response(response)


print(get_weather_sync("London"))

async def main():
    print(await get_weather_async("London"))

asyncio.run(main())
```

1. Shared validation logic
2. Shared response transformation logic
3. Shared logic for building the request
4. Merged function to get URL, headers, and params
5. Synchronous request logic
6. Asynchronous request logic

Voilà, our code is much less duplicated!
But it's still having line repetitions in `get_weather_sync` and `get_weather_async`, because the synchronous version
uses
`httpx.Client()`, whereas the asynchronous version uses `httpx.AsyncClient()`. These are different classes in httpx
designed
for synchronous and asynchronous workflows, respectively.
Consequently, people can say that these repetitions are justified and minimal.

Let's imagine a less successful case:

* You have dozens of functions making requests. All of them have shared logic different to the other endpoints
* In the async version, you have more than one async code section. It forces you to merge code into shared logic again!

Under these conditions, following DRY leads you to the terrible code architecture.
But you cannot ignore code duplication!
Otherwise, to produce small change, you need to apply the same steps multiple times.
To async and sync versions. We will come back to the solution of this issue later.

### Client-side validation

Why should you validate data before accessing the API (client-side validation)?
A better outcome is catching exceptions, thrown due to wrong data, than getting JSON explaining the reason of the error.

Let's imagine the API, wrapping by you to the following request:

```http
POST /create-task HTTP/1.1
Content-Type: application/json

{
    "title": "",
    "description": "This is the description of the important task",
    "dueDate": 1641330000,
    "priority": "crucial"
}
```

Respond like that:

```http
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/json
Content-Length: 1234

{
  "detail": {
    "code": -1,
    "msg": "Invalid data"
  }
}
```    

This is the response to our attempt to create a task in some project-management app.
Why is the data invalid?
We have to find an answer by self due to bad-designed API.
We have been doing it for hours and eureka!

There are three reasons of error:

* Title may not be empty
* Due date must be in the future
* Priority must be on of 'low', 'medium', 'high'

If the users provide invalid data, we have to explain why it is invalid.
Because the users prefer a better designed API, rather than finding a solution to the problem for hours like you.
You should solve this problem instead of an API developer.
You need to validate data and throw an exception when data is invalid.

There is a good approach using `pydantic` framework.
It is intended to perform various validations.
Let's write two versions of code achieving almost the same results.

#### "Vanilla" code:

```python
import httpx
from datetime import datetime
from typing import Any, Literal, get_args

client = httpx.Client(base_url='https://project-managment/api')
Priority = Literal['low', 'medium', 'high']  # (1)!


def create_task(
        title: str,
        due_date: int,
        priority: Priority,
        description: str = None
) -> dict[str, Any]:
    if not isinstance(title, str):
        raise TypeError('Title must be a string')

    if not title:
        raise ValueError('Title may not be empty')

    if len(title) > 120:
        raise ValueError('Max title length is 120')

    if not isinstance(due_date, int):  # (2)!
        raise ValueError('Due date must be integer')

    if datetime.now().timestamp() > due_date:
        raise ValueError('Due date must be in the future')

    if priority not in (values := get_args(Priority)):  # (3)!
        raise ValueError(f'Priority must be from {values}')

    if not isinstance(description, (str, None)):
        raise TypeError('Description must be a string or None')

    if len(description) > 500:
        raise ValueError('Max title length is 500')

    json_ = {
        'title': title,
        'dueDate': due_date,
        'priority': priority,
        'description': description
    }

    response = client.post(url='/create-task', json=json_)
    response.raise_for_status()  # (4)!  
    return response.json()
```

1. Define the possible task priorities using a Literal type
2. Due date represented as a timestamp
3. Validate that the provided priority is one of the defined values, getting possible values of the Priority type
4. Raise an exception for HTTP errors

Don't you find writing such code boring?
What if `/create-task` route would have more parameters?
Let's write code, using `pydantic`!

#### Pydantic version.

```python
import httpx
from datetime import datetime
from typing import Any, Literal, Union
from pydantic.alias_generators import to_camel
from pydantic import BaseModel, field_validator, Field, AliasGenerator, ConfigDict

client = httpx.Client(base_url='https://project-managment/api')
Priority = Literal['low', 'medium', 'high']  #(1)!


class Task(BaseModel):
    model_config = ConfigDict(alias_generator=AliasGenerator(serialization_alias=to_camel))  # (2)!

    title: str = Field(max_length=120)  # (3)!
    due_date: int  # (4)!
    priority: Priority
    description: Union[str, None] = Field(None, max_length=500)  #(5)!

    @field_validator('due_date', mode='before')  #(6)!
    def _validate_date(cls, value: int) -> int:
        if datetime.now().timestamp() > value:
            raise ValueError('Due date must be in the future')  #(7)!
        return value


def create_task(title: str, due_date: int, priority: Priority, description: str = None) -> dict[str, Any]:
    data = Task(title=title, due_date=due_date, priority=priority, description=description)  # (8)!

    data = data.model_dump(mode='json')  #(9)!

    response = client.post(url='/create-task', json=data)
    response.raise_for_status()  #(10)!
    return response.json()
```

1. Define the possible task priorities using a `Literal` type.
2. Configure the model to use camelCase for serialization.
3. Title of the task, limited to 120 characters.
4. Due date represented as a timestamp.
5. Optional description, max 500 characters.
6. Validator to ensure the due date is in the future.
7. Raise an error if due date is not in the future.
8. Create a `Task` instance with provided parameters.
9. Serialize the `Task` instance to JSON format.
10. Raise an exception for HTTP errors.

#### Benefits

Let's compare "vanilla" and `pydantic` versions:

1) The vanilla version requiring throwing an exception in every boilerplate situation.
   The pydantic version only requires throwing an exception when due date is invalid.
   In other cases it validates all automatically, according to type hints and such params as `max_length`.

2) In the vanilla version, we manually set up request parameters(json) and convert name of args, that is `snake_case` to
   `camelCase`. The pydantic version suggests built-in functions for converting cases of arguments and provides the
   possibility
   to set automatic conversion.

3) The pydantic version looks like shorter than the vanilla version.

Even if the API is well-designed and provide understandable error messages, you should perform **client-side
validation**. Furthermore, the data validation before request doesn't require a significant resource allocation.

Here are benefits, accessible when applying client-side validation:

##### Prevents unnecessary requests

If you validate data on the client side, you can stop invalid requests from even reaching the server.
This reduces server load, as fewer incorrect requests are sent, leading to better performance.
Even if you're not a server owner, you're doing a good job for him.

##### Reduced latency

Client-side validation allows users to immediately see if they've made an error, improving the user experience by
avoiding the delay that comes from sending a request to the server and waiting for a response.

##### API Rate Limits

Many APIs enforce [rate limits](https://en.wikipedia.org/wiki/Rate_limiting) to control how frequently clients can make
requests.
By validating client-side, you reduce the chance of consuming API calls with invalid requests, preventing hitting
rate limits unnecessarily.

### Handling Rate Limits

When working with APIs, it's essential to be aware of rate limits that dictate how many requests you can make within a
certain timeframe. Exceeding these limits can result in denied requests, temporary bans, or throttling. Each API has
its own rate limit policies, which are usually documented in the API documentation. To ensure your users that your
API wrapper functions smoothly, consider handling rate limits automatically. 

### Get Relevant response

When interacting with APIs, the response structure isn’t always in the format you’d like to use directly.
Often, APIs return more data than necessary, or they nest the desired data under fields like `data`.
In these situations, transforming the response is crucial to extract only the useful parts and make the API responses
cleaner and more predictable for users of your wrapper.

Let’s explore some common cases when transforming the response to achieve relevance is necessary:

#### Unwrap Primary Data

Many APIs wrap the primary response in a field, such as "data", "results", or "payload".
This is common in REST APIs and GraphQL APIs, where the actual information is nested to allow for metadata, status
codes,
or other details to coexist in the response.

Consider this API response:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "success",
  "data": {
    "user": {
      "id": 123,
      "name": "Alice",
      "email": "alice@example.com"
    }
  }
}
```

In this case, the important part of the response is the user object inside the "data" field.
However, to avoid forced extraction data from nested fields yourself,
you can transform this response by extracting just the "user" data and returning it directly.

Here’s how we would transform it:

```python
import httpx
from typing import Any

client = httpx.Client(base_url='https://domain.com/api')


def get_user(id_: int) -> dict[str, Any]:
   response = client.post(f'/users/{id_}')
   data = response.json()["data"]
   return data.get["user"]
```

This will give you the following transformed response:

```json
{
   "id": 123,
   "name": "Alice",
   "email": "alice@example.com"
}
```

#### Discarding Fields

APIs often return fields that are irrelevant to your wrapper.
Keeping unnecessary fields can make your data harder to manage, increase the payload size unnecessarily and even confuse
users.
In such cases, it’s useful to transform the response by discarding irrelevant fields.

Consider this API response:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "status": "success",
    "data": {
        "id": 789,
        "username": "johndoe",
        "email": "john.doe@example.com",
        "created_at": "2023-09-15T12:34:56Z",
        "updated_at": "2023-10-01T14:45:00Z",
        "is_email_verified": true,
        "internal_metadata": {
            "tracking_id": "abc123",
            "auth_token": "sensitive_token_value",
            "source": "signup_form"
        }
    }
}
```

In this case, internal_metadata contains fields that are irrelevant,
and timestamps such as `created_at` and `updated_at` may not be needed in the client-side logic.
These fields can be discarded during the transformation process.

```python
import httpx
from typing import Any

client = httpx.Client(base_url='https://domain.com/api')


def get_user(id_: int) -> dict[str, Any]:
   response = client.post(f'/users/{id_}')
   data = response.json()["data"]
   to_extract = "id", "username", "email", "is_email-verified"
   return {k: v for k, v in data if k in to_extract}
```

This will give you the following transformed response:

```json
{
   "id": 789,
   "username": "johndoe",
   "email": "john.doe@example.com",
   "is_email-verified": true
}
```

#### Renaming Fields

When working with APIs, you might find that the field names in the response are obscure.
Sometimes, fields need to be renamed for clarity or to meet certain naming conventions.

Consider this API response:

```http
HTTP/1.1 200 OK
Content-Type: application/json
        
{
    "usr_nm": "john_doe",
    "pwd": "secret_password",
    "status": "active"
}
```

Here, the field names are not only unclear but could lead to misunderstandings:

* usr_nm should be renamed to username for clarity.
* pwd is a poor name for a password field.
  It should be renamed to something clear, like password_hash.

* Additionally, the status field might be better understood if it were more descriptive, like account_status.

Let’s transform these poorly named fields into more meaningful ones:

```python
import httpx
from typing import Any

client = httpx.Client(base_url='https://domain.com/api')


def get_user(id_: int) -> dict[str, Any]:
   data = client.post(f'/users/{id_}').json()

   refactoring = {
      'usr_nm': 'username',
      'pwd': 'password',
      'status': 'account_status'
   }

   result = {refactoring[k]: v for k, v in data.items()}
   return result
```

This will give you the following transformed response:

```json
{
   "username": 789,
   "password": "secret_password",
   "account_status": "active"
}
```

In addition to renaming fields for clarity,
it is also common to convert field names from camelCase(or another case) to snake_case to follow Python’s naming
conventions.

///info
Case is the convention used to format the letters and separate words in names of variables, functions, classes,
constants, or other identifiers.
There are some common cases:

1. **snake_case**  
   Lowercase letters with underscores between words (e.g., `my_variable_name`).  
   **Usage:** Common in Python, Ruby, and C for variables, function names.

2. **kebab-case**  
   Lowercase words separated by hyphens (e.g., `my-variable-name`).  
   **Usage** Primarily used in URLs (HTML, CSS classes/IDs).

3. **UPPER_CASE**  
   All uppercase letters with underscores between words (e.g., `CONSTANT_VALUE`).  
   **Usage:** Constants in C, C++, Python, and Java.

4. **camelCase**  
   Starts with a lowercase letter, with each subsequent word capitalized (e.g., `myVariableName`).  
   **Usage:** Common in JavaScript, Java, C#, and object-oriented languages.

5. **PascalCase**  
   Every word starts with a capital letter, no separators (e.g., `MyVariableName`).  
   **Usage:** Used in C#, .NET, Java, and TypeScript for class and type names.

6. **Header-Case**  
   Capitalizes the first letter of each word, separated by hyphens (e.g., `My-Header-Name`).  
   **Usage:** Often seen in HTTP headers and configuration files.

Each case serves to improve readability and consistency depending on language and context.

///

Here’s how you can include this conversion when handling API responses:

Suppose the API response returns fields like userName, passwordHash, and accountStatus.
We can automatically convert these camelCase names to snake_case using a utility function.

Consider this API response:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "userName": "john_doe",
    "password": "secret_password",
    "accountStatus": "active"
}
```

Let's transform the response, converting camelCase to snake_case:

```python
import re
import httpx
from typing import Any

client = httpx.Client(base_url='https://domain.com/api')


def snake_case(s: str) -> str:
   """Convert a string of any case to snake_case. """
   s = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
   s = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s)
   s = re.sub(r'\W+', '_', s).lower()
   s = re.sub(r'_+', '_', s)
   return s


def get_user(id_: int) -> dict[str, Any]:
   data = client.post(f'/users/{id_}').json()

   result = {snake_case(k): v for k, v in data.items()}
   return result
```

This will give you the following transformed response:

```json
{
   "username": 789,
   "password": "secret_password",
   "account_status": "active"
}
```

## Magic

The features just discussed we will call "Golden Rules".
If you wish to merge this features into one tool, I can make you happy!
These rules are the foundation of Sensei framework!

Let's go to [the first steps](/learn/user_guide/first_steps.html) of your learning curve!

!!! example
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
         ) -> list[Self]:  # (1)!
            ...
      
         @classmethod
         @router.get('/users/{id_}')
         def get(cls, id_: Annotated[int, Path(alias='id')]) -> Self:  # (2)!
      
         @router.patch('/users/{id_}', skip_finalizer=True)
         def update(
                 self,
                 name: str,
                 job: str
         ) -> datetime.datetime:  # (3)!
            ...
      
         @update.prepare
         def _update_in(self, args: Args) -> Args:  # (4)!
            args.url = format_str(args.url, {'id_': self.id})
            return args
      
         @update.finalize()
         def _update_out(self,
                         response: Response) -> datetime.datetime:  # (5)!
            json_ = response.json()
            result = datetime.datetime.strptime(json_['updated_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
            self.first_name = json_['name']
            return result
      
         @router.delete('/users/{id_}')
         def delete(self) -> Self:  # (6)!
      
         @delete.prepare
         def _delete_in(self, args: Args) -> Args:  # (7)!
            url = args.url
            url = format_str(url, {'id_': self.id})
            args.url = url
            return args
      
         @router.post('/token')
         def login(self) -> str:  # (8)!
      
         @login.prepare
         def _login_in(self, args: Args) -> Args:  # (9)!
            args.json_['email'] = self.email
            return args
      
         @login.finalize
         def _login_out(self, response: Response) -> str:  # (10)!
            return response.json()['token']
      
         @router.put('/users/{id_}', skip_finalizer=True)
         def change(
                 self,
                 name: Annotated[str, Query()],
                 job: Annotated[str, Query()]
         ) -> bytes:  # (11)!
            ...
      
         @change.prepare
         def _change_in(self, args: Args) -> Args:  # (12)!
            args.url = format_str(args.url, {'id_': self.id})
            return args
      
      ```
      
      1. Framework knows how to handle response
      2. Framework knows how to handle response
      3. Framework does not know how to represent response as datetime object. You need to specify hook.
      4. Get id from current object
      5. Specify hook, to handle response instead of framework
      6. Delete a user
      7. Prepare request for deleting a user
      8. User login
      9. Prepare request for login
      10. Handle login response
      11. Change user details
      12. Prepare request for changing user details
