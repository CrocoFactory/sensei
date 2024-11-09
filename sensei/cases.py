"""
Module containing case converters.

**Case Converter** is a function that takes the string of one case and converts it to the string of another case
and similar structure.

Import them directly from Sensei:

```python
from sensei import camel_case, snake_case, pascal_case, constant_case, kebab_case, header_case
```

They can be applied at different levels:

=== "Router Level"
    ```python
    from sensei import Router, camel_case, snake_case

    router = Router(
        'https://api.example.com',
        body_case=camel_case,
        response_case=snake_case
    )

    @router.post('/users')
    def create_user(first_name: str, birth_city: str, ...) -> User:
        pass
    ```

=== "Route Level"
    ```python
    from sensei import Router, camel_case, snake_case

    router = Router('https://api.example.com')

    @router.post('/users', body_case=camel_case, response_case=snake_case)
    def create_user(first_name: str, birth_city: str, ...) -> User:
        pass
    ```

=== "Routed Model Level"

    ```python
    router = Router(host, response_case=camel_case)

    class User(APIModel):
        def __header_case__(self, s: str) -> str:
            return kebab_case(s)

        @staticmethod
        def __response_case__(s: str) -> str:
            return snake_case(s)

        @classmethod
        @router.get('/users/{id_}')
        def get(cls, id_: Annotated[int, Path(alias='id')]) -> Self: pass
    ```
"""

import re

__all__ = [
    'snake_case',
    'camel_case',
    'pascal_case',
    'constant_case',
    'kebab_case',
    'header_case'
]


def snake_case(s: str) -> str:
    """
    Convert a string to the snake_case.

    Example:
        ```python
        print(snake_case('myParam'))
        ```

        ```text
        my_param
        ```

    Args:
          s (str): The string to convert.
    """
    s = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
    s = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s)
    s = re.sub(r'\W+', '_', s).lower()
    s = re.sub(r'_+', '_', s)
    return s


def camel_case(s: str) -> str:
    """
    Convert a string to the camelCase.

    Example:
        ```python
        print(snake_case('my_param'))
        ```

        ```text
        myParam
        ```

    Args:
          s (str): The string to convert.
    """
    s = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
    s = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s)
    s = re.sub(r'\W+', '_', s)
    words = s.split('_')
    capitalized_words = [word.capitalize() for word in words]
    return capitalized_words[0].lower() + ''.join(capitalized_words[1:])


def pascal_case(s: str) -> str:
    """
    Convert a string to the PascalCase.

    Example:
        ```python
        print(snake_case('my_param'))
        ```

        ```text
        MyParam
        ```

    Args:
          s (str): The string to convert.
    """
    s = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', s)
    s = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s)
    s = re.sub(r'\W+', '_', s)
    words = s.split('_')
    capitalized_words = [word.capitalize() for word in words]
    return ''.join(capitalized_words)


def constant_case(s: str) -> str:
    """
    Convert a string to the CONSTANT_CASE.

    Example:
        ```python
        print(snake_case('myParam'))
        ```

        ```text
        MY_PARAM
        ```

    Args:
          s (str): The string to convert.
    """
    s = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', s)
    s = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s)
    s = re.sub(r'[\W_]+', '_', s)
    return s.upper()


def kebab_case(s: str) -> str:
    """
    Convert a string to the kebab-case.

    Example:
        ```python
        print(snake_case('myParam'))
        ```

        ```text
        my-param
        ```

    Args:
          s (str): The string to convert.
    """
    s = re.sub(r"(\s|_|-)+", " ", s)
    s = re.sub(r"[A-Z]{2,}(?=[A-Z][a-z]+[0-9]*|\b)|[A-Z]?[a-z]+[0-9]*|[A-Z]|[0-9]+",
               lambda mo: ' ' + mo.group(0).lower(), s)
    s = '-'.join(s.split())
    return s


def header_case(s: str) -> str:
    """
    Convert a string to Header-Case.

    Example:
        ```python
        print(snake_case('myParam'))
        ```

        ```text
        My-Param
        ```

    Args:
          s (str): The string to convert.
    """
    s = re.sub('(.)([A-Z][a-z]+)', r'\1 \2', s)
    s = re.sub('([a-z0-9])([A-Z])', r'\1 \2', s)
    s = re.sub(r'[_\W]+', ' ', s)
    words = s.split()
    capitalized_words = [word.capitalize() for word in words]
    return '-'.join(capitalized_words)
