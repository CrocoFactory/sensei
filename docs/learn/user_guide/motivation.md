Imagine you are one of the users using your API Wrapper.
Let's analyze the needs of the users.
We can list the most preferable features desired to be seen by the users:

## Sync and async code versions.

Since **User A** can create a CPU-bound application making few calls of functions from our
wrapper, he does not need to integrate app based on parallelism with three lines of async code.
Moreover, these lines will be evaluated only once per app session.
But **User B** can create an app that most of the time performs
I/O-bound work, consequently his concurrent application will benefit from these lines of async code.

But mostly it's hard to implement both versions of the code, following DRY principle.
Most of the attempts lead to the code duplication or bad code architecture.
Let's show duplicated code example

### Synchronous Example

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
    # Assume we want to extract specific fields from the response
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


# Usage:
print(get_weather_sync("London"))
```

### Asynchronous Example

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


# Usage:
async def main():
    print(await get_weather_async("London"))


asyncio.run(main())
```

### Deduplicated version

Let's try to implement both versions and apply minimal duplication(deduplication), merging code into shared logic.

```python
import httpx
import asyncio
from httpx import Response, Client, AsyncClient
from typing import Any, Union

BaseClient = Union[Client, AsyncClient]
Components = tuple[str, dict[str, Any], dict[str, Any]]


# Shared validation logic
def validate_params(city: str, units: str) -> None:
    if not city:
        raise ValueError("City name cannot be empty")
    if units not in {"metric", "imperial"}:
        raise ValueError("Units must be 'metric' or 'imperial'")


# Shared response transformation logic
def transform_response(response: Response) -> dict[str, Any]:
    data = response.json()
    return {
        "city": data["name"],
        "temperature": data["main"]["temp"],
        "description": data["weather"][0]["description"]
    }


# Shared logic for building the request
def build_request(client: BaseClient, url: str, params: dict, headers: dict) -> Response:
    return client.get(url, params=params, headers=headers)


# Merged function to get URL, headers, and params
def get_components(city: str, units: str) -> Components:
    url = "https://api.openweathermap.org/data/2.5/weather"
    headers = {"Accept": "application/json"}
    params = {"q": city, "units": units, "appid": "your_api_key"}
    return url, headers, params


# Synchronous version
def get_weather_sync(city: str, units: str = "metric") -> dict[str, Any]:
    validate_params(city, units)

    url, headers, params = get_components(city, units)

    # Synchronous request logic
    with httpx.Client() as client:
        response = build_request(client, url, params, headers)
        return transform_response(response)


# Asynchronous version
async def get_weather_async(city: str, units: str = "metric") -> dict[str, Any]:
    validate_params(city, units)

    url, headers, params = get_components(city, units)

    # Asynchronous request logic
    async with httpx.AsyncClient() as client:
        response = await build_request(client, url, params, headers)
        return transform_response(response)


# Usage for sync
print(get_weather_sync("London"))


# Usage for async
async def main():
    print(await get_weather_async("London"))


asyncio.run(main())
```

Voilà, our code is much less duplicated!
But it's still having line repetitions in `get_weather_sync` and `get_weather_async`, because the synchronous version
uses
httpx.Client(), whereas the asynchronous version uses httpx.AsyncClient(). These are different classes in httpx designed
for synchronous and asynchronous workflows, respectively.
Consequently, people can say that these repetitions are justified and minimal.

Let's imagine a less successful case:

* You have dozens of functions making requests. All of them have shared logic different to the other endpoints
* In the async version, you have more than one async code section. It forces you to merge code into shared logic again!

Under these conditions, following DRY leads you to the terrible code architecture.
But you cannot ignore code duplication!
Otherwise, to produce small change, you need to apply the same steps multiple times.
To async and sync versions. We will come back to the solution of this issue later.

## Client-side validation

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

### "Vanilla" code:

```python
import httpx
from datetime import datetime
from typing import Any, Literal, get_args

client = httpx.Client(base_url='https://project-managment/api')
Priority = Literal['low', 'medium', 'high']  # Define the possible task priorities using a Literal type


def create_task(title: str, due_date: int, priority: Priority, description: str = None) -> dict[str, Any]:
    if not isinstance(title, str):
        raise TypeError('Title must be a string')

    if not title:
        raise ValueError('Title may not be empty')

    if len(title) > 120:
        raise ValueError('Max title length is 120')

    if not isinstance(due_date, int):  # Due date represented as a timestamp
        raise ValueError('Due date must be integer')

    if datetime.now().timestamp() > due_date:
        raise ValueError('Due date must be in the future')

    # Validate that the provided priority is one of the defined values
    if priority not in (values := get_args(Priority)):  # Get possible values of the Priority type
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
    response.raise_for_status()  # Raise an exception for HTTP errors
    return response.json()
```

Don't you find writing such code boring?
What if `/create-task` route would have more parameters?
Let's write code, using `pydantic`!

### Pydantic version.

```python
import httpx
from datetime import datetime
from typing import Any, Literal, Union
from pydantic.alias_generators import to_camel
from pydantic import BaseModel, field_validator, Field, AliasGenerator, ConfigDict

client = httpx.Client(base_url='https://project-managment/api')
Priority = Literal['low', 'medium', 'high']  # Define the possible task priorities using a Literal type


# Define the Task model using Pydantic for data validation and serialization
class Task(BaseModel):
    # Configure the model to use camelCase for serialization
    model_config = ConfigDict(alias_generator=AliasGenerator(serialization_alias=to_camel))

    title: str = Field(max_length=120)  # Title of the task, limited to 120 characters
    due_date: int  # Due date represented as a timestamp
    priority: Priority
    description: Union[str, None] = Field(None, max_length=500)  # Optional description, max 500 characters

    # Validator to ensure the due date is in the future
    @field_validator('due_date', mode='before')
    def _validate_date(cls, value: int) -> int:
        if datetime.now().timestamp() > value:
            raise ValueError('Due date must be in the future')  # Raise error if due date is not in the future
        return value  # Return the validated due date


def create_task(title: str, due_date: int, priority: Priority, description: str = None) -> dict[str, Any]:
    # Create a Task instance with provided parameters
    data = Task(title=title, due_date=due_date, priority=priority, description=description)

    # Serialize the Task instance to JSON format
    data = data.model_dump(mode='json')

    response = client.post(url='/create-task', json=data)
    response.raise_for_status()  # Raise an exception for HTTP errors
    return response.json()
```

### Comparison versions

Let's compare "vanilla" and `pydantic` versions:

1) The vanilla version requiring throwing an exception in every template situation.
   The pydantic version only requires throwing an exception when due date is invalid.
   In other cases it validates all automatically, according to type hints and such params as `max_length`.

2) In the vanilla version, we manually set up request parameters(json) and convert name of args, that is `snake_case` to
   `camelCase`. The pydantic version suggests built-in functions for converting cases of arguments and provides the
   possibility
   to set automatic conversion.

3) The pydantic version looks like shorter than the vanilla version.

### Benefits

Even if the API is well-designed and provide understandable error messages, you should perform **client-side
validation**. Furthermore, the data validation before request doesn't require a significant resource allocation.

Here are benefits, accessible when applying client-side validation:

#### Prevents unnecessary requests

If you validate data on the client side, you can stop invalid requests from even reaching the server.
This reduces server load, as fewer incorrect requests are sent, leading to better performance.
Even if you're not a server owner, you're doing a good job for him.

#### Reduced latency

Client-side validation allows users to immediately see if they've made an error, improving the user experience by
avoiding the delay that comes from sending a request to the server and waiting for a response.

#### API Rate Limits

Many APIs enforce [rate limits](https://en.wikipedia.org/wiki/Rate_limiting) to control how frequently clients can make
requests.
By validating client-side, you reduce the chance of consuming API calls with invalid requests, preventing hitting
rate limits unnecessarily.

## Handling Rate Limits

When working with APIs, it's essential to be aware of rate limits that dictate how many requests you can make within a
certain timeframe. Exceeding these limits can result in denied requests, temporary bans, or throttling. Each API has
its own rate limit policies, which are usually documented in the API documentation. To ensure your users that your
API wrapper functions smoothly, consider handling rate limits automatically. 
